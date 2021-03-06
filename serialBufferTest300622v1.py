import datetime
import logging
import math
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os
import RPi.GPIO as GPIO
import serial # https://pyserial.readthedocs.io/en/latest/pyserial_api.html
import struct
from subprocess import call
import sys
import threading
import time
from time import sleep
from time import perf_counter
import MUPsettings
import random



time1 = startTime = time.time()


### Zmienne globalne
#MUPsettings.init()
Addr = ""      # Adres mastera9
LenD = 00      # Dlugosc ramki
Coml = 00      # Dopelnienie LenD
MSB = 0000       # msb
LSB = 0000       # lsb
FByte = ""  # msb + lsb
bitCnt = 0    # Licznik dlugosci ramki
CR_flag = 0   # Flaga znaku '\r'
checksum = 0  # Poprawnosc odebranej ramki
WH = ""
WL = ""
WRD = ""
Data = ""
start = 0
startTime = 0
timeRecv = 0
noDataTimer = 0
SR = b''
fram = ""
inactiveUARTflag = 0
strBuffer = b''
strBuffer2 = b''
stopRec = 0

# Parametry czasowe # Ustawic w lepiej dostepnym miejscu do latwej zmiany parametrow
T1 = 3 # 60-600s
T2 = 30 # 10-120min -> 600-7200s
timer = 0
timer_flag = 0
timer_flag2 = 0

##################### Inicjalizacja programu #####################
# Inicjalizacja portu ttyNVT0
call('sudo ttynvt -M 199 -m 6 -n ttyNVT0 -S 156.17.14.245:22029', shell=True)
sleep(0.1)

# Inicjalizacja połączenia z serwerem portów
SerialData = serial.Serial("/dev/ttyNVT0",115200)




def USARTctrl():
    global strBuffer, strBuffer2, stopRec
    cnt = 0
    while True:
        print(len(strBuffer2))
#         start3 = time.time()
        if len(strBuffer) > 0:
            stopRec = 1
            strBuffer2 += strBuffer
            strBuffer = b''
#             print(strBuffer2)
            
        char = strBuffer2[0:]
        cnt += 1
        strBuffer2 = strBuffer2[1:len(strBuffer2)]
        stopRec = 0
#         print(time.time()-start3)

USART_thread = threading.Thread(target = USARTctrl)
USART_thread.start()

while True:
    start2 = time.time()
    if SerialData.inWaiting() > 0 and stopRec == 0:
        SR = SerialData.read(SerialData.inWaiting())
        timeSR = time.time() - startTime
        strBuffer += SR
#         print(strBuffer)#[-1:]
#         print(time.time()-start2)
