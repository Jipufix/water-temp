import machine
import time
import uasyncio as asyncio
import aioble
import bluetooth
import struct
import ds18x20
from onewire import OneWire
from machine import ADC, Pin
from ssd1306 import SSD1306_I2C

# BLE Configuration
BLE_DEVICE_NAME = "TempMon"
SERVICE_UUID = bluetooth.UUID("af65f22f-0b5c-4ac5-a2a1-76606258c2b0")
CHARACTERISTIC_UUID = bluetooth.UUID("19b10001-e8f2-537e-4f6c-d104768a1214")

# Digit drawing functions
DIGITS = {
    "0": ["#####", "#   #", "#   #", "#   #", "#####"],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", "#####"],
    "2": ["#####", "    #", "#####", "#    ", "#####"],
    "3": ["#####", "    #", "#####", "    #", "#####"],
    "4": ["#   #", "#   #", "#####", "    #", "    #"],
    "5": ["#####", "#    ", "#####", "    #", "#####"],
    "6": ["#####", "#    ", "#####", "#   #", "#####"],
    "7": ["#####", "    #", "   # ", "  #  ", "  #  "],
    "8": ["#####", "#   #", "#####", "#   #", "#####"],
    "9": ["#####", "#   #", "#####", "    #", "#####"],
    ".": ["     ", "     ", "     ", "     ", "  #  "]
}

# Constants Setup
THRESHOLD_MIN = 104.0
THRESHOLD_MAX = 120.0
threshold = THRESHOLD_MIN
OBSERVED_MIN = 180
OBSERVED_MAX = 3200

# Hardware Setup
i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4), freq=100000)
oled = SSD1306_I2C(128, 64, i2c)
temp_pin = machine.Pin(2)
knob = ADC(Pin(1))
red_led = machine.Pin(11, machine.Pin.OUT)
green_led = machine.Pin(9, machine.Pin.OUT)

# Potentiometer Setup
knob.atten(ADC.ATTN_11DB)  # Full 0-3.3V range

# DS18B20 Initialization
ow = OneWire(temp_pin)
ds = ds18x20.DS18X20(ow)
roms = ds.scan()
if not roms:
    print("No DS18B20 sensors found!")
    raise SystemExit

# BLE Service Setup
temp_service = aioble.Service(SERVICE_UUID)
temp_characteristic = aioble.Characteristic(
    temp_service,
    CHARACTERISTIC_UUID,
    read=True,
    notify=True,
    capture=False
)
aioble.register_services(temp_service)

# Resolution Configuration
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
    
# Arduino-style map function for MicroPython
def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

# Convert from C to F
def c_to_f(temp):
    return temp * 1.8 + 32



# Temperature reading
async def read_temp():
    ds.convert_temp()
    await asyncio.sleep_ms(750)
    return ds.read_temp(roms[0])

def draw_huge_digit(oled, char, x, y):
    pattern = DIGITS.get(char, [" "]*5)
    for row in range(5):
        for col in range(5):
            if pattern[row][col] == "#":
                for dx in range(3):
                    for dy in range(3):
                        oled.pixel(x + col*4 + dx, y + row*6 + dy, 1)

def draw_huge_text(oled, text, x, y):
    for i, char in enumerate(text):
        draw_huge_digit(oled, char, x + i*24, y)

# BLE Advertising
async def ble_advertise():
    while True:
        try:
            # Add manufacturer data to force full UUID advertisement
            async with await aioble.advertise(
                250_000,
                name=BLE_DEVICE_NAME,
                services=[SERVICE_UUID],
                manufacturer=(0xFFFF, b'\x00'),  # Forces 128-bit UUID inclusion
                appearance=0,
            ) as connection:
                print("Client connected:", connection.device)
                await connection.disconnected()
                print("Client disconnected")
        except Exception as e:
            print("Advertising error:", e)
            await asyncio.sleep_ms(1000)

# Main temperature update loop
async def update_display():
    last_temp = None
    global threshold     # in F
    while True:
        temp = await read_temp()
        temp = c_to_f(temp)
        
        # Update threshold from potentiometer
        raw_value = knob.read()
        new_threshold = map_value(raw_value, OBSERVED_MIN, OBSERVED_MAX, THRESHOLD_MIN, THRESHOLD_MAX)
        if new_threshold != threshold:
            threshold = new_threshold
        
        # Update LEDs
        if temp >= threshold:
            red_led.on()
            green_led.off()
        else:
            red_led.off()
            green_led.on()
        
        # Update display
        oled.fill(0)
        # Draw temperature in large digits
        draw_huge_text(oled, f"{int(temp)}", 0, 20)
        # Draw threshold in top right corner, small font
        oled.text(f"THR:{int(threshold)}", 60, 0, 1)
        oled.show()
        last_temp = temp
        
        
        # BLE message
        payload = struct.pack("<ff", temp, threshold)  # Little-endian, 8 bytes total
        try:
            temp_characteristic.write(payload, send_update=True)
            print(f"Sent: {temp}°F, {threshold}°F")
        except Exception as e:
            print("BLE write failed:", e)


        

# Main async loop
async def main():
    advert_task = asyncio.create_task(ble_advertise())
    display_task = asyncio.create_task(update_display())
    await asyncio.gather(advert_task, display_task)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Shutting down")
    machine.reset()
