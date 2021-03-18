# EyeSight controller
# For children's ride-on toys
# C Hyzer (TJBChris) wrote this: 11/18/2016

print("\npwEyeSight Controller")
print("(C)2016 Christopher Hyzer (TJBChris).  All Rights Reserved.  Licensed via GPLv3.  See LICENSE.TXT")
print("\nEyeSight and Subaru are trademarks of Subaru of America, Inc. and are used for reference puproses only.\n")

# Imports
import Adafruit_MCP9808.MCP9808 as MCP9808
from gps3.agps3threaded import AGPS3mechanism
import time
import can
from lidar_lite import Lidar_Lite
import smbus
import _thread
import RPi.GPIO as GPIO

# GPIO 19 = Low Speed
# GPIO 26 = High Speed
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Relay outputs
GPIO.setup(19, GPIO.OUT)
GPIO.setup(26, GPIO.OUT)

# Sensor inputs
GPIO.setup(5, GPIO.IN) # 12v voltage divider input / REVERSE
GPIO.setup(6, GPIO.IN) # 12v voltage divider input / THROTTLE
GPIO.setup(13, GPIO.IN) # 12v voltage divider input
GPIO.setup(16, GPIO.IN) # 3.3v Pi-Powered / ES OFF Switch
GPIO.setup(20, GPIO.IN) # 3.3v Pi-Powered Sensor

# Variables for data to be consumed by the CAN stream.
# Distance is in feet; speed is in *SCALE* MPH
# Raw
speed = 0
distance = 0
reverse = False 
highSpeed  = False
throttle = False
battTemp = 0
lastDistance = 999
lvsaTriggered = False
hadTarget = False

# EyeSight Switch debounce
switchCount = 0

# PCW/PCB thresholds (in feet)
esWarn = 14
esFirst = 9.1
esSecond = 9 

# Lead Vehicle Distances
esFollowOne = 16
esFollowTwo = 30
esFollowThree = 45

# CAN (Tach will be controlled by the CAN thread as it is emulated
# CAN 0D1
canSpdMSB = 0
canSpdLSB = 0
# CAN 167
esObstacleData = 0
# CAN 166
# 0x00 = no "OFF" indicators, 0x01 = PCB OFF, 0x02 = LDW OFF, 0x03 = both OFF
esEnable = 0x00
# CAN 166
esFollowDst = 0x00
# CAN 360 Byte 4: 90 Center scale, FE = Top of scale, FF = Pegged, 59 = C (first line on scale)
canTemp = 0x59
# CAN 148 - Gear - 1B = Drive, 0x1D = Reverse
gear = 0x1B

# VEH indicator added to Eyesight Counter: 4 = VEH on/brake lights off, 12 = VEH on, brake lights on
# Modifier also controls Lane Keep Assist indicator
esCtModifier = 4
# Lead Vehicle: 0 = off, 64 = on
esLeadVehicle = 64

# Define the function for the CAN stream thread.
def canStream (name):
	# Init
	print ("CAN stream initializing")
	bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
	print ("CAN stream intialized.")
	#notifier = can.Notifier(bus, [can.Printer()])
	esCounter = 0
	tachVal = 2500
	tachCycle = 1 # Pretend we have shift points based on cycle
	odoClick = 0
	odoCount = 0

	# Begin CAN stream
	while True:

		# Determine what the tach should read and click the odometer
		if throttle == False:
			if tachVal != 700:
				tachVal = tachVal - 5
				tachCycle = 1

		if throttle == True and reverse == True:
			odoCount = odoCount + 1
			if tachVal != 1300:
				if tachVal > 1300:
					tachVal = tachVal - 5
				else:
					tachVal = tachVal + 5
		if throttle == True and reverse == False and esObstacleData != 11:
			odoCount = odoCount + 1
			if tachCycle == 1:
				if tachVal != 3400:
					if tachVal < 3400:
						tachVal = tachVal + 5
					else:
						tachVal = tachVal - 5
				else:
					tachVal = 1800
					tachCycle = tachCycle + 1
			if tachCycle == 2:
				if tachVal != 3800:
					if tachVal < 3800:
						tachVal = tachVal + 5
					else:
						tachVal = tachVal - 5
				else:
					tachVal = 1700
					tachCycle = tachCycle + 1
			if tachCycle == 3:
				if tachVal != 2800:
					if tachVal < 2800:
						tachVal = tachVal + 5
					else:
						tachVal = tachVal - 5
				else:
					tachVal = 1500
					tachCycle = 4
			if tachCycle == 4:
				if tachVal != 1750:
					if tachVal < 1750:
						tachVal = tachVal + 5
					else:
						tachVal = tachVal - 5

		# Emergency braking = automatic idle
		if throttle == True and reverse == False and esObstacleData == 11:
			tachVal = 700

		# Calculate the tachometer byte values
		tachTemp = int((tachVal/16)+5)
		tachByte1 = (tachTemp % 16)  * 16
		tachByte2 = int((tachTemp - (tachTemp % 16)) /16)

		if odoCount > 50:
			odoClick = 4
			odoCount = 0

		try:
			bus.send(can.Message(extended_id=False,arbitration_id=0x188,data=[0x00,0x00,0x0C,0x00,0x01,0x07,0x00,0x00]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x0D3,data=[0x00,0x00,0x00,0x00,0x00,odoClick,0x00]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x0D1,data=[canSpdLSB,canSpdMSB,0x00,0x04]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x0D2,data=[0x00,0x00,0xFF,0xFF,0x00,0x00,0x2E,0x2F]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x370,data=[0x00,0x00,0x10,0x00,0x00,0x00,0x00,0x00]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x372,data=[0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x360,data=[0x00,0x04,0x00,canTemp,0x00,0x30,0x00,0x36]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x361,data=[0x00,0x20,0x00,0x00,0x00,0x00,0x00,0x00]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x148,data=[gear,0x10,0x00,0x00,0x00,0x00,0x00,0x20]))
			bus.flush_tx_buffer()
			bus.send(can.Message(extended_id=False,arbitration_id=0x166,data=[esEnable,0x10,esFollowDst,int(distance),esCounter,esLeadVehicle,0x00,0x00]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x167,data=[0x00,0x00,0x00,0x00,0x00,0x00,esObstacleData,0x00]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x25C,data=[0x20,0x00,0x00,0x00,0x00,0x00,0x00,0x00]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x141,data=[0x00,0x00,0x00,0x00,tachByte1, tachByte2,0x00,0x00]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x0D3,data=[0x00,0x00,0x00,0x00,0x00,odoClick,0x00]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x0D1,data=[canSpdLSB,canSpdMSB,0x00,0x04]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x0D3,data=[0x00,0x00,0x00,0x00,0x00,0x00,0x00]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x144,data=[0x00,0x01,0x53,0x37,0x16,0xA8,0x08,0x00]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x368,data=[0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00]))
			bus.send(can.Message(extended_id=False,arbitration_id=0x374,data=[0x48,0x00,0x00,0x00,0x00,0x00,0x00,0x00]))
			# EyeSight requires a counter increment by thirty-two in 14 increments, then restart at zero
			esCounter = esCounter + 32
			if esCounter > 255:
				esCounter = 0 + esCtModifier

			bus.flush_tx_buffer()
			# Reset the Odometer clicker
			odoClick = 0

			#print ("loop ends")
		except:
			pass

try:
	_thread.start_new_thread(canStream,("can-thread",))
except:
	print("Unable to start CAN thread.")

# Temp sensor init
#print("Initializing temperature sensor")
#sensor = MCP9808.MCP9808()
#sensor.begin()
#print("Temperature sensor init complete")

# GPS Init
print("Initializing GPS.")
agps_thread = AGPS3mechanism()
agps_thread.stream_data()
agps_thread.run_thread()
print("GPS init complete.")

# LIDAR Init
print("Initializing LIDAR.")
lidar = Lidar_Lite()
connected = lidar.connect(1)
print ("LIDAR initialized.")

print ("\nStarting control loop.")
while True:

	# Get the temp data
	# 13C (55F) is 0 point for battery temp
	#temp = sensor.readTempC()
	#if temp < 13:
	#	temp = 13
	
	#canTemp = int((temp + 30) * 2.2)
	#print("CAN Temp: " + str(canTemp))
	#if canTemp > 255:
	#	canTemp = 255
	canTemp = 0x90
	# Get the speed from the GPS
	if agps_thread.data_stream.speed != "n/a":
		# GPS data is in m/s, converted to miles per hour (2.23694) and scaled to 20x
		speed = int(agps_thread.data_stream.speed * 2.23694 * 20)
		speedval = int(speed / .5625)
		if speedval < 16:
			canSpdMSB = 0
			canSpdLSB = (speedval  % 16) * 16
		else:
			#speedval[3:4]+"00"+speedval[2:3]
			canSpdLSB = (speedval % 16) * 16 
			canSpdMSB = int((speedval - (speedval % 16))/16) 

		#print("Speed: " + str(speed) + ", LSB: " + str(canSpdLSB) + ", MSB: " + str(canSpdMSB))

	# Get the EyeSight OFF switch input
	if GPIO.input(16):
		switchCount = switchCount + 1
		if switchCount > 8:
			if esEnable == 0x00:
				esEnable = 0x01
				switchCount = 0
			else:
				esEnable = 0x00
				switchCount = 0
	else:
		switchCount = 0

	# Get pedal and gear selection
	# Gear
	if GPIO.input(13):
		reverse = True
	else:
		reverse = False

	# Throttle (which wire varies whether car is in Reverse or not)
	if reverse == True:
		if GPIO.input(5):
			throttle = True
			if esObstacleData == 10 or esObstacleData == 11:
				esObstacleData = 0
		else:
			throttle = False
			if esObstacleData == 10 or esObstacleData == 11:
				esObstacleData = 0
	else:
		if GPIO.input(6) == False:
			throttle = True
		else:
			throttle = False	
			if esObstacleData == 10 or esObstacleData == 11:
				esObstacleData = 0

	# Gear display
	if reverse == True:
		gear = 0x1D	
	else:
		gear = 0x1B

	# For Lead Vehicle Start Alert - track lowest distance achieved while throttle is not pressed.
	if throttle == True:
		lastDistance = 0
		lvsaTriggered = False
		if esObstacleData == 0x04:
			esObstacleData = 0

	# Get the distance.
	try:
		distance = lidar.getDistance()/30.48
		prevDst = distance
	except:
		distance = prevDst 
		pass
	#print("LD: " + str(lastDistance) + ", D: " + str(distance)) 

	# Set lowest distance to object if throttle is false and a forward gear is chosen
	if throttle == False and lvsaTriggered == False and reverse == False:
		if lastDistance == 0:
			lastDistance = distance

		if distance < lastDistance:
			lastDistance = distance
	
		if distance - lastDistance > 15:
			#print("Vehicle ahead has moved")
			lvsaTriggered = True
			esObstacleData = 0x04

	if esObstacleData == 0x01:
		esObstacleData = 0x00

	if distance <= 0.1:
		lastDistance = 0
		lvsaTriggered = False

	# Pre-collision warning and automatic braking
	# Show/hide lead vehicle indicator and beep when target status changes
	#print("Distance: " + str(distance))
	if distance  > 80 or distance <= 0.1:
		esFollowDst = 0x81
		esLeadVehicle = 0
		if hadTarget == True:
			esObstacleData = 0x01
		hadTarget = False
		esCtModifier = 4
		GPIO.output(26, GPIO.LOW)
		GPIO.output(19, GPIO.LOW)
		if esObstacleData != 0x04 and esObstacleData != 0x01:
			esObstacleData = 0
	else:
		esLeadVehicle = 64
		if hadTarget == False:
			esObstacleData = 0x01
		hadTarget = True

	if distance > 0.1 and distance <= esFollowOne:
		if (distance < esSecond) and esEnable == 0x00:
			GPIO.output(26, GPIO.HIGH)
			if reverse == False:
				GPIO.output(19, GPIO.HIGH)
				esCtModifier = 12
				if throttle == True:
					esObstacleData = 11
			else:
				GPIO.output(19, GPIO.LOW)
				esCtModifier = 4
		if (distance >= esSecond and distance < esFirst ) and esEnable == 0x00:
			GPIO.output(26, GPIO.HIGH)
			GPIO.output(19, GPIO.LOW)
			esCtModifier = 4
			if reverse == False:
				#esCtModifier = 12
				if throttle == True:
					esObstacleData = 10
			else:
				esCtModifier = 4
		if (distance >= esFirst and distance < esWarn) and esEnable == 0x00:
			GPIO.output(26, GPIO.LOW)
			GPIO.output(19, GPIO.LOW)
			esCtModifier = 4
			if reverse == False:
				if throttle == True:
					esObstacleData = 10
		esFollowDst = 0x21
		# If PCB is disabled, force relays off
		# A 0x00 value is ES disabled (ES OFF ENABLE)
		if esEnable != 0x00:
			GPIO.output(26, GPIO.LOW)
			GPIO.output(19, GPIO.LOW)
		if distance >= esWarn and esEnable == 0x00:
			esCtModifier = 4
			GPIO.output(26, GPIO.LOW)
			GPIO.output(19, GPIO.LOW)
			if esObstacleData != 0x04 and esObstacleData != 0x01:
				esObstacleData = 0 
	if distance >= esFollowOne and distance < esFollowTwo:
		GPIO.output(26, GPIO.LOW)
		GPIO.output(19, GPIO.LOW)
		esCtModifier = 4
		if esObstacleData != 0x04 and esObstacleData != 0x01:
			esObstacleData = 0
		esFollowDst = 0x41
	if distance >= esFollowTwo and distance < esFollowThree:
		GPIO.output(26, GPIO.LOW)
		GPIO.output(19, GPIO.LOW)
		esCtModifier = 4
		esFollowDst = 0x61
		if esObstacleData != 0x04 and esObstacleData != 0x01:
			esObstacleData = 0
	if distance >= esFollowThree:
		esCtModifier = 4
		GPIO.output(26, GPIO.LOW)
		GPIO.output(19, GPIO.LOW)
		if esObstacleData != 0x04 and esObstacleData != 0x01:
			esObstacleData = 0
		esFollowDst = 0x81
	#time.sleep(.15)
