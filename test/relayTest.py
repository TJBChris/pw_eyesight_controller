import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(19, GPIO.OUT)


while True:
	GPIO.output(19, GPIO.HIGH)
	time.sleep(1)
	GPIO.output(19, GPIO.LOW)
	GPIO.output(19, GPIO.LOW)
	time.sleep(1)
