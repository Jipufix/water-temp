import machine
import time
from onewire import OneWire
import ds18x20
from ssd1306 import SSD1306_I2C

# Unsafe temperature threshold (in Celsius)
THRESHOLD = 40.0

# I2C setup for SSD1315 OLED (128x64)
i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4), freq=100000)
oled = SSD1306_I2C(128, 64, i2c)

# Pin configuration
datapin = machine.Pin(2)  # Data pin for DS18B20
red_led = machine.Pin(11, machine.Pin.OUT)
green_led = machine.Pin(9, machine.Pin.OUT)

# Initialize OneWire and DS18B20
ow = OneWire(datapin)
ds = ds18x20.DS18X20(ow)

roms = ds.scan()
if not roms:
    print("No DS18B20 sensors found!")
    raise SystemExit

# Set resolution to 9-bit (fastest conversion)
def set_resolution(rom, res_bits):
    assert res_bits in (9, 10, 11, 12)
    config = {9: 0x1F, 10: 0x3F, 11: 0x5F, 12: 0x7F}[res_bits]
    ow.reset()
    ow.select_rom(rom)
    ow.writebyte(0x4E)  # Write scratchpad
    ow.writebyte(0x4B)  # TH register
    ow.writebyte(0x46)  # TL register
    ow.writebyte(config)  # Configuration register

for rom in roms:
    set_resolution(rom, 9)

# Read temperature
def read_temp():
    ds.convert_temp()
    time.sleep_ms(94)
    return ds.read_temp(roms[0])

# Large digit patterns
DIGITS = {
    "0": [" ### ",
          "#   #",
          "#   #",
          "#   #",
          " ### "],
    "1": ["  #  ",
          " ##  ",
          "  #  ",
          "  #  ",
          " ### "],
    "2": [" ### ",
          "#   #",
          "   # ",
          "  #  ",
          "#####"],
    "3": [" ### ",
          "#   #",
          "  ## ",
          "#   #",
          " ### "],
    "4": ["   # ",
          "  ## ",
          " # # ",
          "#####",
          "   # "],
    "5": ["#####",
          "#    ",
          "#### ",
          "    #",
          "#### "],
    "6": [" ### ",
          "#    ",
          "#### ",
          "#   #",
          " ### "],
    "7": ["#####",
          "   # ",
          "  #  ",
          " #   ",
          " #   "],
    "8": [" ### ",
          "#   #",
          " ### ",
          "#   #",
          " ### "],
    "9": [" ### ",
          "#   #",
          " ####",
          "    #",
          " ### "],
    ".": ["     ",
          "     ",
          "     ",
          "     ",
          "  #  "],
}

# Draw one large character
def draw_huge_digit(oled, char, x, y):
    pattern = DIGITS.get(char, ["     "]*5)
    for row in range(5):
        for col in range(5):
            if pattern[row][col] == "#":
                for dx in range(3):
                    for dy in range(3):
                        oled.pixel(x + col * 4 + dx, y + row * 6 + dy, 1)

# Draw a whole large string
def draw_huge_text(oled, text, x, y):
    for i, char in enumerate(text):
        draw_huge_digit(oled, char, x + i * 24, y)

# Main loop
while True:
    temp = read_temp()
    print("Temp:", temp)

    # Update LEDs
    if temp >= THRESHOLD:
        red_led.on()
        green_led.off()
        danger_text = "DANGER"
    else:
        red_led.off()
        green_led.on()
        danger_text = ""

    # Draw on OLED
    oled.fill(0)
    
    # Draw "DANGER" text in yellow if temp is too high
    if danger_text:
        oled.text(danger_text, 10, 0, 1)  # Draw "DANGER" in yellow (top area)
    
    # Draw the temperature value in the bottom (blue area)
    draw_huge_text(oled, "{:.1f}".format(temp), 0, 20)
    
    oled.show()

    time.sleep(1)
