import smbus
import time
from lidar_lite import Lidar_Lite

lidar = Lidar_Lite()
connected = lidar.connect(1)

while True:
	print(lidar.getDistance())
	time.sleep(1)
