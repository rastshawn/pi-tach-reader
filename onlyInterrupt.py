from datetime import datetime
import RPi.GPIO as GPIO
import time
import threading
import os



###### This section manages reading the tach signals and assigns them to g_rpm
g_rpm = 1000 #holds the most recent RPM reading

GPIO.setmode(GPIO.BCM) # what does this do
GPIO.setwarnings(False) # why
tachInputPin = 17
GPIO.setup(tachInputPin, GPIO.IN, GPIO.PUD_DOWN)

fps = 3 #must be at least 2
dt = datetime.now()



# every time there's a pulse, this calculates the rpm and sets g_rpm
def pulseInterrupt(channel):
    global dt
    global g_rpm
    nt = datetime.now()
    timediff = nt - dt
    dt = nt
    
    MICROSECONDS_IN_ONE_MINUTE = 6000000.0
    g_rpm = int((MICROSECONDS_IN_ONE_MINUTE/timediff.microseconds) * 5)

    # this is what things should look like if I applied my understanding, 
    # which is clearly wrong
    # g_rpm = MICROSECONDS_IN_ONE_MINUTE / (timediff.microseconds * 2)

GPIO.add_event_detect(tachInputPin, GPIO.RISING, callback=pulseInterrupt)

# dummy interrupt code
dx = 1
def simulateRPMchange():
    global dx, g_rpm
    if g_rpm > 6000 or  g_rpm < 900:
        dx = -dx
    g_rpm = g_rpm + dx
    threading.Timer(0.001, simulateRPMchange).start()
#simulateRPMchange()


##### main loop
#while True:
#    print(g_rpm)

print('time, rpm')
startTime = datetime.now()
def printRow():
    print(f'{(datetime.now()-startTime).total_seconds()}, {g_rpm}')
    threading.Timer(0.05, printRow).start()

printRow()


