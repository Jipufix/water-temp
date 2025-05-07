import uasyncio as asyncio
import aioble
import bluetooth
from machine import Pin

SERVICE_UUID = bluetooth.UUID("af65f22f-0b5c-4ac5-a2a1-76606258c2b0")
CHARACTERISTIC_UUID = bluetooth.UUID("19b10001-e8f2-537e-4f6c-d104768a1214")
LED_PIN = 4

led = Pin(LED_PIN, Pin.OUT)
led.off()

async def ble_receiver():
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
                    # Get data directly from notification
                    data = await char.notified()
                    try:
                        temp = float(data.decode().strip())
                        print(f"🌡️ Temp: {temp}°C")
                        led.value(temp >= 40.0)
                    except Exception as e:
                        print(f"⚠️ Parse error: {e}")
                        led.off()

            except Exception as e:
                print(f"Connection failed: {e}")
            finally:
                await connection.disconnect()
                print("🔌 Disconnected")
                
        except Exception as e:
            print(f"Scan failed: {e}")
            await asyncio.sleep(5)

asyncio.run(ble_receiver())
