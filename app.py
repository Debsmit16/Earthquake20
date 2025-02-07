from flask import Flask, render_template, send_file, jsonify
from mcculw import ul
from mcculw.enums import ULRange
import threading
import time
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend for Matplotlib
import matplotlib.pyplot as plt
import io
import firebase_admin
from firebase_admin import credentials, db
import logging

# Firebase initialization
cred = credentials.Certificate('/C:/Users/User/Downloads/earthquake-bed2e-firebase-adminsdk-fbsvc-fb37054b32.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://earthquake-bed2e-default-rtdb.asia-southeast1.firebasedatabase.app'
})

# Get reference to Firebase database
ref = db.reference('earthquake_data')
alerts_ref = db.reference('alerts')

app = Flask(__name__)

# Configuration
board_num = 0  # The board number, usually 0 for the first device
channel = 0  # The analog input channel
ai_range = ULRange.BIP5VOLTS  # The range of the analog input

# Local data storage for plotting
data = []

# Add logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('seismic_monitor.log'),
        logging.StreamHandler()
    ]
)

# Function to read sensor data
def read_sensor_data():
    value = ul.a_in(board_num, channel, ai_range)
    return value

# Background thread to read data
def data_acquisition():
    while True:
        try:
            seismic_data = read_sensor_data()
            if seismic_data > 0:  # Ensure valid data is read
                # Update local data for plotting
                data.append(seismic_data)
                if len(data) > 100:
                    data.pop(0)

                # Store data in Firebase
                ref.push({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'value': seismic_data
                })

                # Check for alert condition
                if seismic_data > 2100.0:  # Example threshold
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    alert_message = f'Seismic Alert! High vibration detected at {current_time} at Sensor 1'
                    print(alert_message)
                    
                    # Store alert in Firebase
                    alerts_ref.push({
                        'timestamp': current_time,
                        'message': alert_message
                    })

                logging.info(f"Seismic data recorded: {seismic_data}")
            else:
                logging.warning(f"Invalid seismic data: {seismic_data}")

            time.sleep(0.1)  # Delay to simulate real-time data acquisition
        except Exception as e:
            logging.error(f"Error in data acquisition: {e}")
            time.sleep(5)  # Wait before retrying

# Start the data acquisition in a separate thread
threading.Thread(target=data_acquisition, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plot.png')
def plot_png():
    fig, ax = plt.subplots()
    try:
        ax.plot(data, label='Vibration')
        ax.axhline(y=2100.0, color='r', linestyle='-', label='Threshold')
        ax.set_xlabel('Time')
        ax.set_ylabel('Vibration Level')
        ax.set_title('Seismic Data')
        ax.legend()
    except Exception as e:
        print(f"Error creating plot: {e}")

    output = io.BytesIO()
    plt.savefig(output, format='png')
    plt.close(fig)
    output.seek(0)
    return send_file(output, mimetype='image/png')

@app.route('/alerts')
def get_alerts():
    # Fetch alerts from Firebase
    alerts_data = alerts_ref.get()
    if alerts_data:
        return jsonify([alert['message'] for alert in alerts_data.values()])
    return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)
