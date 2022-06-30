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



### Analiza danych z ramki cd ###
def readFrameData(adress):
    global start, Data, bitCnt, termAtd, termBtd, termCtd, ADC1td, RTCtd, F1td, F2td, WDStd, CPRtd, SHARP30td, SR04td, TempLists, DailyData
 
    print(Data)
#
    # Termometr A
    if adress == '01': # DS18B20 | 1bit = 0,0625*C | Zakres: (-50) ... (+125) | FC90 - 07D0 (HEX) | Rozdzielczość 1K
        # Mozna dodac obsluge bledow - sprawdzenie czy dane mieszcza sie w zakresie | z drugiej strony uzytkownik sam moze okreslic czy dany pomiar jest prawidlowy - moze to swiadczyc o problemie z czujnikiem
        str2int = int(Data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
        # DO ZROBIENIA - Wyznaczenie wartosci ujemnych
        pomiar = str2int * 0.0625
        termAtd.append(pomiar)
        return

#
    # Termometr B
    elif adress == '02': # Pt1000 | 1bit = ... | Zakres: 0...250 | Rozdzielczość 1K (max) | dane temp?
        str2int = int(Data,16) # str > int > obliczenie wartosci: 1*C na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        termBtd.append(pomiar)

#
    # Termometr C
    elif adress == '12': # LM35 | 1bit = ... | Zakres: 0...100
        str2int = int(Data,16) # str > int > obliczenie wartosci: 1*C na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        termCtd.append(pomiar)
        
# 
    # WDS
    elif adress == '0C': # WDS-1000-MP-C3-P
        str2int = int(Data,16) # str > int > obliczenie wartosci: 1x na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        WDStd.append(pomiar)
        
# 
    # CPR
    elif adress == '08': # CPR240
        str2int = int(Data,16) # str > int > obliczenie wartosci: 1x na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        CPRtd.append(pomiar)
        return
    
# 
    # SHARP30
#     elif adress == '0D': # GP2Y0A41SK0F
#         str2int = int(Data,16) # str > int > obliczenie wartosci: 1x na bin
#         pomiar = str2int * 1 # Do podmienienia przelicznik
#         SHARP30td.append(pomiar)
#         return
    
# 
    # SR04
    elif adress == '0E': # HC-SR04
        str2int = int(Data,16) # str > int > obliczenie wartosci: 1x na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        SR04td.append(pomiar)
        return
    
# 
    # F1
    elif adress == '06': # Belka tensometryczna NA27 | podaje wartośćśrednią W | brak WL WH | 
#         print(Data)
        str2int = int(Data,16) # str > int > obliczenie wartosci: 1x na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        F1td.append(pomiar)
        return
    
# 
    # F2
    elif adress == '07': # SparkFun HX711
        str2int = int(Data,16) # str > int > obliczenie wartosci: 1x na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        F2td.append(pomiar)
        return
    
# 
    # RTC
    elif adress == '05':
#         print(Data)
#         str2int = int(Data,16) # str > int > obliczenie wartosci: 1x na bin
#         pomiar = str2int * 1 # Do podmienienia przelicznik
#         RTCtd.append(pomiar)
        return
    
# 
    # ADC1
    elif adress == '03':
#         print(Data)
#         str2int = int(Data,16) # str > int > obliczenie wartosci: 1x na bin
#         pomiar = str2int * 1 # Do podmienienia przelicznik
#         ADC1td.append(pomiar)
        return
    
#
    # Zabezpieczenie przed bledami
    else:
        # Podglad dodaatkowych adresow
        print(str(adress) + " #")
#         return


def checkFrame(A):
    global Addr, LenD, ComL, MSB, LSB, FByte, bitCnt, CR_flag, checksum, Data, SR2hex, startTime, timeRecv
#     timeRecv = perf_counter()
#     print(bitCnt)
#     print(A)
    ## Znak /n
    if A == 10:
        # Sprawdz poprawnosc ramki (czy wystapil wczesniej znak CR)
        if CR_flag == 1:
            # Okreslenie prawidlowej dlugosci ramki (ilosc wyrazow * 4bity na wyraz + 6 bitow wiodacych + 2 bity koncowe + przesuniecie licznika w dol jako liczenie od zera)
#             frameLen = int(LenD,16)*4+6+2-1
#             print(frameLen)
#             print(bitCnt)
            frameLen=15
            # Sprawdz czy ramka ma poprawna dlugosc
            if frameLen == bitCnt:
                checksum = 1 # Ramka poprawna
                CR_flag = 0  # Wyzerowanie flagi
                readFrameData(Addr) # Addr, Data # W tym przypadku watek checkFrame czeka niepotrzebnie? na wykonanie wywolanej funkcji - wprowadzenie zmiennej globalnej i przerwania od zmiany wartosci zmiennej?
                Data = ""
            else:
                checksum = -1 # Ramka nieprawidlowa
                print(str(Addr) + " | Ramka nieprawidlowa - niepoprawna dlugosc ramki")
        else:
            checksum = -1 # Ramka nieprawidlowa
            print(str(Addr) + " | Ramka nieprawidlowa - brak CR")

        # Wyzeruj licznik ramki
        bitCnt = 0

    # Znak /r
    elif A == 13:
        # Aktywuj flage, zwieksz licznik
        if (bitCnt - 6) % 4 == 0:
            CR_flag = 1
            bitCnt += 1
        else:
            checksum = -1
            print(str(Addr) + " | Ramka nieprawidlowa - niepoprawna dlugosc danych ramki przed znakiem CR")

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
#             print(A)
            bitCnt += 1
            if bitCnt > 6: # Laczenie bajtow w dane
                Data += SR.decode("ascii")
            else: # Laczenie bajtow w dwuznakowy HEX
                if bitCnt % 2 == 1:
                    MSB = tohex(A,4)
                else:
                    LSB = tohex(A,4)
                    FByte = str(MSB[2:]) + str(LSB[2:])
#                     print(FByte)
            
            ## Sprawdz byte

            # Adres
            if bitCnt == 2:
                Addr = FByte
#                 print(Addr)

            # Dlugosc ramki
            elif bitCnt == 4:
                LenD = FByte
#                 print(LenD)

            # ComL
            elif bitCnt == 6:
                ComL = FByte
#                 print(ComL)
    


def tohex(val, nbits): # Przelicz int na hex
  return hex((val + (1 << nbits)) % (1 << nbits))


while True:
    timeRecv = perf_counter()
    checkFrame(18+30)
    checkFrame(18+43)
    checkFrame(18+30)
    checkFrame(18+31)
    checkFrame(18+46)
    checkFrame(18+46)
    checkFrame(18+30)
    checkFrame(18+30)
    checkFrame(18+30)
    checkFrame(18+30)
    checkFrame(18+30)
    checkFrame(18+30)
    checkFrame(18+30)
    checkFrame(18+30)
    checkFrame(13)
    checkFrame(10)
    print(perf_counter() - timeRecv)
