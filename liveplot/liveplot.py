import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import math
import os
import select

# 1. Create a figure with 1 row and 2 columns of subplots
fig, axs = plt.subplots(1, 2, figsize=(10, 4))


xs = []
yrolls = []
ypitchs = []

deg = 0
prev="0,0,0"


file = os.open("/tmp/drone-attitude.pipe",os.O_RDONLY | os.O_NONBLOCK)

def nextPipedAttitute(f):
    ready_to_read, _, _ = select.select([f], [], [], 0)
    if ready_to_read:
        data = os.read(f, 1024)
        if not data:
                return None
        else:
                return data.decode('utf-8').strip()
    else:
         return None



# This function is called periodically from FuncAnimation
def animate(i, xs, yrolls, ypitchs):
    deg = i

    prev = nextPipedAttitute(file)

    if prev is None:
         return

    lines = prev.splitlines()


    for line in lines:

        nums = line.split(",")

        deg = int(nums[0])
        yroll = round(float(nums[1]),3)
        ypitch = round(float(nums[2]),3)

        xs.append(deg)
        yrolls.append(yroll)
        ypitchs.append(ypitch)

        # Limit x and y lists to 360 items 
        xs = xs[-360:]
        yrolls = yrolls[-360:]
        ypitchs = ypitchs[-360:]

    # Draw x and y lists
    axs[0].clear()
    
    axs[0].set_title('Roll')
    axs[0].set_xlabel('X axis')
    axs[0].set_ylabel('Y axis')

    axs[0].plot(xs, yrolls)

    axs[1].clear()
    axs[1].set_title('Pitch')
    axs[1].set_xlabel('X axis')
    axs[1].set_ylabel('Y axis')

    axs[1].plot(xs, ypitchs)

# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig, animate, fargs=(xs, yrolls,ypitchs), interval=100,cache_frame_data=False)
plt.tight_layout()
plt.show()
