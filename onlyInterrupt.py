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
stringBuffer = []
headerString = 'time, rpm, throttle'
stringBuffer.append(headerString + '\n')
BATCH_LENGTH = 20
outputFolder = 'output'
print(headerString)
startTime = datetime.now()

# Read the output folder to sequentially create filenames for the current session
# Creates the outputfolder if it doesn't exist
# Creates "Run_(n+1).csv" if "Run_(n).csv" exists.
# Creates "Run_1.csv" if none are found.
def getNextFilename(outputFolder):
    # Check if the output folder exists, if not, create it
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)

    # Get the list of existing files in the output folder
    existingFiles = [f for f in os.listdir(outputFolder) if os.path.isfile(os.path.join(outputFolder, f))]

    # Find the highest number from existing file list
    maxRunNumber = 0
    for filename in existingFiles:
        if filename.startswith("Run_") and filename.endswith(".csv"):
            try:
                runNumber = int(filename.split("_")[1].split(".")[0])
                maxRunNumber = max(maxRunNumber, runNumber)
            except ValueError:
                pass  # Ignore filenames that don't match the expected pattern

    # Increment the run number for the new file
    nextRunNumber = maxRunNumber + 1

    # Construct the new filename
    newFilename = f"Run_{nextRunNumber}.csv"
    return os.path.join(outputFolder, newFilename)

filename = getNextFilename(outputFolder)

def addToWriteQueue(string):
    global stringBuffer
    stringBuffer.append(string)
    if len(stringBuffer) > BATCH_LENGTH:
        with open(filename, 'a') as f:
            stringToWrite = ''.join(stringBuffer)
            f.write(stringToWrite)
            stringBuffer = []

def printRow():    
    runningSeconds = (datetime.now()-startTime).total_seconds()
    tpsRawValue = adc.read_adc(0, gain=GAIN)
    if tpsRawValue < TPS_0_PERCENT:
        tpsRawValue = TPS_0_PERCENT
    elif tpsRawValue > TPS_100_PERCENT:
        tpsRawValue = TPS_100_PERCENT
    tpsRangedValue = tpsRawValue - TPS_0_PERCENT

    tpsPercent = 100 * (tpsRangedValue / TPS_RANGE)  # todo. Maybe autoset max and min?
    
    rowString = f'{(datetime.now()-startTime).total_seconds()}, {g_rpm}, {tpsPercent}'
    print(rowString)
    addToWriteQueue(rowString + '\n')
    threading.Timer(0.05, printRow).start()
    
printRow()


