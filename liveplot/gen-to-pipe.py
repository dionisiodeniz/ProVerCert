import math
import time

def nextY(t):
    t = t % 360
    rad = math.radians(t)
    return t,math.sin(rad),math.cos(rad)

with open("/tmp/drone-attitude.pipe", "w") as file:
    for i in range(1,720):
        n,s,c = nextY(i)
        file.write(str(i)+","+str(s)+","+str(c)+"\n")
        file.flush()
        time.sleep(0.05)
