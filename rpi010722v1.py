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








def checkFrame(A):
    global Addr, LenD, ComL, MSB, LSB, FByte, bitCnt, CR_flag, checksum, Data, SR2hex, startTime, timeRecv
    timeRecv = perf_counter()

    ## Znak /n
    if A == 10:
        # Wyzeruj licznik ramki
        bitCnt = 0

    # Znak /r
    elif A == 13:
        bitCnt += 1

    # Pozostale elementy ramki
    else:
        # Sprawdz poprawnosc znakow (czy sa HEXami)
        A -= 48 # Czy sa to znaki 0-9
        if A > 16:
            A -= 7 # Czy sa to znaki A-F
        if A > 16: # Jesli nadal poza zakresem -> nie sa HEXem
            checksum = -1 # Ramka nieprawidlowa            
        else:  # Znaki poprawne -> dalsza analiza ramki

            # Polacz znaki
            bitCnt += 1
            if bitCnt > 6: # Laczenie bajtow w dane
                Data += SR.decode("ascii")
            else: # Laczenie bajtow w dwuznakowy HEX
                if bitCnt % 2 == 1:
                    MSB = SR.decode("ascii")
                else:
                    LSB = SR.decode("ascii")
                    FByte = str(MSB) + str(LSB)
            
            ## Sprawdz byte

            # Adres
            if bitCnt == 2:
                Addr = FByte

            # Dlugosc ramki
            elif bitCnt == 4:
                LenD = FByte

            # ComL
            elif bitCnt == 6:
                ComL = FByte
    print(perf_counter() - timeRecv)


def tohex(val, nbits): # Przelicz int na hex
  return hex((val + (1 << nbits)) % (1 << nbits))


##################### Watki rownolegle #####################
def USARTctrl():
    global strBuffer, strBuffer2, stopRec
    cnt = 0
    while True:
#         print("Buf1: " + str(len(strBuffer)) + " | Buf2: " + str(len(strBuffer2)))
#         start3 = time.time()
        if len(strBuffer) > 0:
            stopRec = 1
            strBuffer2 += strBuffer
            strBuffer = b''
            print(strBuffer2)
            
        char = strBuffer2[0:]
        cnt += 1
        strBuffer2 = strBuffer2[1:len(strBuffer2)]
        stopRec = 0
        SR2hex = SR.hex()
        SR2int = int(SR2hex, 16)
        checkFrame(SR2int)
#         print(time.time()-start3)

USART_thread = threading.Thread(target = USARTctrl)
USART_thread.start()

while True:
#     start2 = time.time()
    if SerialData.inWaiting() > 0 and stopRec == 0:
        SR = SerialData.read(SerialData.inWaiting())
        timeSR = time.time() - startTime
        strBuffer += SR
#     print(time.time()-start2)

