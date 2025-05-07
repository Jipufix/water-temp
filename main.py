import machine
import time
from onewire import OneWire
import ds18x20

# Pin configuration
datapin = machine.Pin(4)  # Data pin for DS18B20
red_led = machine.Pin(5, machine.Pin.OUT)
green_led = machine.Pin(6, machine.Pin.OUT)

THRESHOLD = 25.0

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
    set_resolution(rom, 9)  # Fastest: ~94ms

# Read temperature
def read_temp():
    ds.convert_temp()
    time.sleep_ms(94)  # Wait for 9-bit conversion
    return ds.read_temp(roms[0])

# Fast loop
while True:
    temp = read_temp()
    print("Temp:", temp)
    if temp >= THRESHOLD:
        red_led.on()
        green_led.off()
    else:
        red_led.off()
        green_led.on()
