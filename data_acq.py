from mcculw import ul
from mcculw.enums import ULRange
import matplotlib.pyplot as plt
import time
from datetime import datetime

# Configuration
board_num = 0  # The board number, usually 0 for the first device
channel = 0  # The analog input channel
ai_range = ULRange.BIP5VOLTS  # The range of the analog input

# Data storage
data = []

# Initialize plot
plt.ion()
fig, ax = plt.subplots()

# Function to read sensor data
def read_sensor_data():
    value = ul.a_in(board_num, channel, ai_range)
    return value

# Function to plot data
def plot_data(data):
    ax.clear()
    ax.plot(data, label='Vibration')
    ax.axhline(y=2100.0, color='r', linestyle='-', label='Threshold')
    ax.set_xlabel('Time')
    ax.set_ylabel('Vibration Level')
    ax.set_title('Seismic Data')
    ax.legend()
    plt.draw()
    plt.pause(0.1)

# Main loop to read data and update plot
try:
    while True:
        seismic_data = read_sensor_data()
        data.append(seismic_data)

        # Keep only the last 100 data points for plotting
        if len(data) > 100:
            data.pop(0)

        plot_data(data)

        # Check for alert condition
        if seismic_data > 2100.0:  # Example threshold
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'Seismic Alert! High vibration detected at {current_time} at Sensor 1')

        time.sleep(0.1)  # Delay to simulate real-time data acquisition
except KeyboardInterrupt:
    print("Exiting program...")
