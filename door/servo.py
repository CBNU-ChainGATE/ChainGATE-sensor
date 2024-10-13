import time
import random
import RPi.GPIO as GPIO

print("Servo Motor Test")
print("Stop is Keyboard Ctrl + C")

# White : Pin 12 : 18(PWM)
# RED   : Pin 2  : 5v
# Black : Pin 14 : GND
GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.OUT)
# 17, 100, 195
phz = GPIO.PWM(26, 100)
phz.start(5)

while True:
    angle = int(input("Angle: "))
    duty = float(angle) / 10.1 + 4.1
    phz.ChangeDutyCycle(duty)
    time.sleep(0.5)
GPIO.cleanup()
