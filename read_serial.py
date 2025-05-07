import serial
import matplotlib.pyplot as plt
import time

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
        print("Serial says:", line)

        if "Temp:" in line:
            try:
                temp_str = line.split("Temp:")[1].strip()
                temp = float(temp_str)

                temps.append(temp)
                times.append(time.time() - start_time)

                line_plot.set_data(times, temps)
                ax.relim()
                ax.autoscale_view()

                plt.draw()
                plt.pause(0.05)

            except ValueError:
                print("Couldn't parse temperature from:", line)
                continue

except KeyboardInterrupt:
    print("Plotting stopped by user (Ctrl+C).")

finally:
    ser.close()
    plt.ioff()
    plt.show()
