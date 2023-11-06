from datetime import datetime
import RPi.GPIO as GPIO
import time
import threading
import os
import Adafruit_ADS1x15 # for TPS ADC


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


###### Set up TPS ADC
# Default gain is 1, for +/-4.096V. Because the ADS1115 is powered at 3.3v,
# max actual input is 3.6v
GAIN = 1
adc = Adafruit_ADS1x15.ADS1115()
TPS_0_PERCENT = 800
TPS_100_PERCENT = 5650
TPS_RANGE = TPS_100_PERCENT - TPS_0_PERCENT

# set up csv header 
print('time, rpm, throttle')
startTime = datetime.now()

def printRow():    
    runningSeconds = (datetime.now()-startTime).total_seconds()
    tpsRawValue = adc.read_adc(0, gain=GAIN)
    if tpsRawValue < TPS_0_PERCENT:
        tpsRawValue = TPS_0_PERCENT
    elif tpsRawValue > TPS_100_PERCENT:
        tpsRawValue = TPS_100_PERCENT
    tpsRangedValue = tpsRawValue - TPS_0_PERCENT

    tpsPercent = 100 * (tpsRangedValue / TPS_RANGE)  # todo. Maybe autoset max and min?
    print(f'{(datetime.now()-startTime).total_seconds()}, {g_rpm}, {tpsPercent}')
    threading.Timer(0.05, printRow).start()
    
printRow()


