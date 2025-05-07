import serial
import matplotlib.pyplot as plt
import time

ser = serial.Serial('COM3', 115200, timeout=1)

temps = []
times = []
start_time = time.time()

# Create the plot and keep it persistent
plt.ion()
fig, ax = plt.subplots()
line_plot, = ax.plot([], [], label="Temp (°C)", color='blue')
ax.set_xlabel("Time (s)")
ax.set_ylabel("Temperature (°C)")
ax.set_title("Live Temperature Data")
ax.legend()

print("Listening for temperature data...")

try:
    while True:
        line = ser.readline().decode().strip()
        print("Serial says:", line)

        if "Temp:" in line:
            try:
                temp_str = line.split("Temp:")[1].strip()
                temp = float(temp_str)

                temps.append(temp)
                times.append(time.time() - start_time)

                # Update plot without clearing
                line_plot.set_data(times, temps)
                ax.relim()  # Recalculate limits based on new data
                ax.autoscale_view()  # Auto-scale the view

                plt.draw()  # Draw the updated plot
                plt.pause(0.05)  # Shorter pause for faster updates

            except ValueError:
                print("Couldn't parse temperature from:", line)
                continue

except KeyboardInterrupt:
    print("Plotting stopped by user.")
    ser.close()
    plt.ioff()
    plt.show()
