# EyeSight controller
# For children's ride-on toys
# C Hyzer (TJBChris) wrote this: 11/18/2016

print("\npwEyeSight Controller")
print("(C)2016 Christopher Hyzer (TJBChris).  All Rights Reserved.")
print("\nEyeSight and Subaru are trademarks of Subaru of America, Inc. and are used for reference puproses only.\n")

# Imports
import time
import can
import _thread
import sys

speed = 0
distance = 0
reverse = False 
highSpeed  = False
throttle = False
battTemp = 0

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
# Value of 4 = show my veh, 0 = no veh
esCtModifier = 0
# Lead Vehicle: 0 = off, 64 = on
esLeadVehicle = 0 

# Define the function for the CAN stream thread.
def canStream (name):
	# Init
	print ("CAN stream initializing")
	bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
	print ("CAN stream intialized.")
	#notifier = can.Notifier(bus, [can.Printer()])
	esCounter = 2
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
		if throttle == True and reverse == False:
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

getch = ""
 
print ("\nStarting demo loop.")
while True:
	# No display
	while getch == "":
		getch = sys.stdin.read(1)
	print("Adaptive Cruise Now")
	getch = ""

	# Adaptive Cruise
	esCtModifier = 4
	# Lead Vehicle: 0 = off, 64 = on
	esLeadVehicle = 0
	esFollowDst = 0x71
	distance = 0x41

	while getch == "":
		getch = sys.stdin.read(1)
	print("Key pressed")
	getch = ""

	esCtModifier = 6

	while getch == "":
		getch = sys.stdin.read(1)
	getch = ""

	# Veh Ahead Has Moved
	esCtModifier = 0
	esFollowDst = 0x00
	distance = 0
	esObstacleData = 0x04

	while getch == "":
		getch = sys.stdin.read(1)
	print("Key pressed")
	getch = ""

	# Lane Departure Warning
	esObstacleData = 0x17
	time.sleep(3)
	esObstacleData = 0x00

	while getch == "":
		getch = sys.stdin.read(1)
	print("Key pressed")
	getch = ""

	# Lane Sway Alert
	esObstacleData = 0x19
	time.sleep(3)
	esObstacleData = 0x00

	while getch == "":
		getch = sys.stdin.read(1)
	getch = ""

	# Obstacle Detected
	esObstacleData = 0x0A

	while getch == "":
		getch = sys.stdin.read(1)
	getch = ""

	esObstacleData = 0x0B

	time.sleep(2)
	esObstacleData = 0x0C

	time.sleep(2)

	esObstacleData = 0x00	
