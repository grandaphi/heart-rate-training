from bleak import BleakScanner, BleakClient
import asyncio as aio
import bleakheart as bh
import matplotlib.pyplot as plt
import numpy as np

# dev_name = "galaxy watch6"
hrm_pro_mac = "EA:C3:29:29:8D:FA"


async def find_devices():
    print("Find devices.")
    devices = await BleakScanner.discover(return_adv=True)
    print(devices)
    # for device, adv_data in devices:
    #     print(device.address , device.name)

async def connect_to_device(dev_name):
    # device= await BleakScanner.find_device_by_filter(lambda dev, adv: dev.name and dev_name in dev.name.lower())
    # if device==None: 
    #     print("Polar device not found")
    client= BleakClient(dev_name)
    await client.connect()
    if not client.is_connected:
        print("Connection failed")
    else:
        print(f"Connected to {client.address}")
        print(f"Client name {client.name}")
    return client

# Define the display function
def display(data):
    print(f"Heart rate: {data}")

# Update the plot with new data
async def update_plot(queue: aio.Queue):
    plt.ion()  # Turn on interactive mode
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    line, = ax.plot([], [], label='Heart Rate', linewidth=0.5)
    ax.set_xlim(0, 200)
    ax.set_ylim(50, 210)
    ax.set_xlabel('Time')
    ax.set_ylabel('Heart Rate')
    ax.set_title('Heart Rate')

    # Define heart rate zones
    zones = [
    ( 50,   90, 'lightblue', 'Warmup'),
    ( 91, 109, 'darkgreen', 'Zone 1'),
    (110, 127, 'lightgreen', 'Zone 2'),
    (128, 145, 'yellow', 'Zone 3: Cardio'),
    (146, 163, 'orange', 'Zone 4: Anaerobic'),
    (164, 220, 'red', 'Zone 5: Max')]

    # Add heart rate zones
    for lower, upper, color, label in zones:
        ax.axhspan(lower, upper, facecolor=color, alpha=0.5)
        ax.text(0.5, (lower + upper) / 2, label, ha='center', va='center', fontsize=12, alpha=0.5, transform=ax.get_yaxis_transform())



    
    # Initial draw
    fig.canvas.draw()
    background = fig.canvas.copy_from_bbox(ax.bbox)
    data = []
    time_sec_in_zones = {
                        "warmup" : 0,
                        "zone_1" : 0,
                        "zone_2" : 0,
                        "zone_3" : 0,
                        "zone_4" : 0,
                        "zone_5" : 0
                         }
    
    hr = int(0)

    while True:
        while len(data) > 200:  # Keep only the last 200 data points
            data.pop(0)
        if not queue.empty():
            item = await queue.get()
            print(f'item type {type(item)}')
            if isinstance(item, tuple):
                print(f" Dequeued item {item[2][0]}")
                data.append(item[2][0])
                hr = item[2][0]
                for i,(min_val,max_val,_,_) in enumerate(zones):
                    zone_key = f"zone_{i}"
                    if i == 0 and hr <= max_val:
                        time_sec_in_zones["warmup"] += 1
                        break
                    if hr >= min_val and hr <= max_val:
                        time_sec_in_zones[zone_key] += 1
                        break
                for zone, time in time_sec_in_zones.items():
                    print(f"Time s in {zone}: {time}.")


            queue.task_done()

            if data:
                line.set_xdata(np.arange(len(data)))
                line.set_ydata(data)
                
                # Restore the background
                fig.canvas.restore_region(background)
                
                # Redraw only the line
                ax.draw_artist(ax.patch)
                ax.draw_artist(line)
                
                # Update the canvas
                fig.canvas.blit(ax.bbox)
                fig.canvas.flush_events()
                print(f"plot data: {data}")
        await aio.sleep(0.5)

async def main():
    client = await connect_to_device(hrm_pro_mac)
    heart_rate_queue = aio.Queue()
    heartrate = bh.HeartRate(client, queue = heart_rate_queue, instant_rate=False, unpack=False)
    await heartrate.start_notify()
    await update_plot(heart_rate_queue)

    # await find_devices()



aio.run(main())

#  queue = heart_rate_queue, 