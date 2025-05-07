import serial
import matplotlib.pyplot as plt
import time

# Setup serial connection
ser = serial.Serial('COM3', 115200, timeout=1)

temps = []
times = []
start_time = time.time()

plt.ion()
fig, ax = plt.subplots()
line_plot, = ax.plot([], [], label="Temp (°C)", color='blue')
ax.set_xlabel("Time (s)")
ax.set_ylabel("Temperature (°C)")
ax.set_title("Live Temperature Data")
ax.legend()

print("Listening for temperature data...")
stop_requested = False

def on_key(event):
    global stop_requested
    if event.key == 'q':
        stop_requested = True
        print("Stopping plot (key 'q' pressed).")

fig.canvas.mpl_connect('key_press_event', on_key)

try:
    while not stop_requested:
        line = ser.readline().decode().strip()
        if "Temp:" in line:
            try:
                temp_str = line.split("Temp:")[1].strip()
                temp = float(temp_str)
                current_time = time.time() - start_time

                # Append new data
                temps.append(temp)
                times.append(current_time)

                # Keep only the last 10 seconds of data
                while times and (current_time - times[0]) > 10:
                    times.pop(0)
                    temps.pop(0)

                # Update plot data
                line_plot.set_data(times, temps)
                ax.set_xlim(max(0, current_time - 10), current_time)
                ax.relim()
                ax.autoscale_view(scalex=False)  # Only autoscale y-axis

                plt.draw()
                plt.pause(0.001)

            except ValueError:
                print("Couldn't parse temperature from:", line)

except KeyboardInterrupt:
    print("Plotting stopped by user (Ctrl+C).")

finally:
    ser.close()
    plt.ioff()
    plt.show()