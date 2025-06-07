import uasyncio as asyncio
import aioble
import bluetooth
import struct
from machine import Pin

# Existing hardware and BLE setup (matches ESP32C6 configuration[3])
SERVICE_UUID = bluetooth.UUID("af65f22f-0b5c-4ac5-a2a1-76606258c2b0")
CHARACTERISTIC_UUID = bluetooth.UUID("19b10001-e8f2-537e-4f6c-d104768a1214")
VALVE_PIN = 4
RESET_PIN = 15

valve = Pin(VALVE_PIN, Pin.OUT)
valve.off()
button = Pin(RESET_PIN, Pin.IN, Pin.PULL_UP)
tripped = False  # Shared state flag

async def watch_button():
    global tripped
    while True:
        if button.value() == 0:  # Active-low button press
            print("Reset button pressed")
            tripped = False
            valve.off()
            # Debounce logic
            while button.value() == 0:
                await asyncio.sleep(0.1)
            await asyncio.sleep(0.1)
        await asyncio.sleep(0.05)

async def ble_receiver():
    global tripped
    while True:
        try:
            print("\n--- Starting BLE scan ---")
            async with aioble.scan(10000) as scanner:
                target = None
                async for result in scanner:
                    if SERVICE_UUID in result.services():
                        print(f"✅ Found device: {result.name()}")
                        target = result.device
                        break
                
                if not target:
                    print("🔍 No device found")
                    await asyncio.sleep(2)
                    continue

            print("\n--- Connecting ---")
            connection = await target.connect(timeout_ms=10_000)
            
            try:
                print("🔗 Discovering services...")
                service = await connection.service(SERVICE_UUID)
                char = await service.characteristic(CHARACTERISTIC_UUID)
                await char.subscribe(notify=True)
                
                print("🚀 Ready for data")
                while True:
                    data = await char.notified()
                    try:
                        if len(data) == 8:
                            temp, threshold = struct.unpack("<ff", data)
                            print(f"🌡️ Current: {temp} | Threshold: {threshold}")
                            
                            # latch trigger
                            if temp >= threshold:
                                tripped = True
                        else: # invalid daya
                            tripped = False

                        valve.value(tripped)

                    except Exception as e:
                        print(f"Data error: {e}")
                        tripped = False
                        valve.off()
            
            except Exception as e:
                print(f"Connection error: {e}")
            finally:
                await connection.disconnect()
                print("🔌 Disconnected")

        except Exception as e:
            print(f"Scan error: {e}")
            await asyncio.sleep(5)

async def main():
    await asyncio.gather(ble_receiver(), watch_button())

asyncio.run(main())
