import numpy as np
import time
from time import sleep
# import matplotlib
import matplotlib.pyplot as plt

timer = 0
tArray = []
yArray = []

x = np.linspace(0, 2, 11)
y = [0,0,0,0,0,0,0,0,0,0,0]

plt.ion()

fig = plt.figure()
ax = fig.add_subplot(111)
line1, = ax.plot(x,y,'y-')

while True:
    
    for i in range(100):
        timer += 1
        yval = pow(2,1/(i+1))
        line1.set_ydata(yval)
        fig.canvas.draw()
        fig.canvas.flush_events()
#         tArray.append(timer)
#         yArray.append(yval)
        sleep(.2)
        plt.scatter(timer,yval)
#         plt.plot(tArray, yArray)
        plt.ylabel('Testing plots')
#     plt.show()
    
#     plt.scatter([1,2,4,5,7],[0,9,12,5,3])
        
        
    timer = 0
