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
SR = ""
fram = ""
inactiveUARTflag = 0

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
    #port = 'COM3',
    #baudrate = 115200#,
    #bytesize = serial.EIGHTBITS,
    #parity = serial.PARITY_NONE,
    #stopbits = serial.STOPBITS_ONE






### Skladanie bajtu ###                                          >> OK
def merge2byte(C):
    global MSB, LSB, FByte, bitCnt, SR
    
    if bitCnt % 2 == 1:
        MSB = SR.decode("ascii")
    else:
        LSB = SR.decode("ascii")
#         FByte = hex((MSB << 8) | LSB)
        FByte = str(MSB) + str(LSB)
#         print(FByte)
    return;



### Skladanie slowa ###
def merge2word(B): # Mozliwe polaczenie z funkcja merge2byte - mniej zmiennych, kod oparty na 'Data += ' z ifami
    global Data
    
    Data += SR.decode("ascii")
    return;



### Odczyt ramki ###  > Brak odczytu poczatkowej ramki; odczyt rozpoczety od wykrycia znaku /n sprawdza ramke od pola adresu do tego znaku
def checkFrame(A):
    global Addr, LenD, ComL, MSB, LSB, FByte, bitCnt, CR_flag, checksum, Data, SR2hex, startTime, timeRecv
#     print(A)
#     timeRecv = time.time()

    ## Znak /n
    if A == 10:

        # Sprawdz poprawnosc ramki (czy wystapil wczesniej znak CR)
        if CR_flag == 1:
            # Okreslenie prawidlowej dlugosci ramki (ilosc wyrazow * 4bity na wyraz + 6 bitow wiodacych + 2 bity koncowe + przesuniecie licznika w dol jako liczenie od zera)
            frameLen = int(LenD,16)*4+6+2-1
            
            # Sprawdz czy ramka ma poprawna dlugosc
            if frameLen == bitCnt:
                checksum = 1 # Ramka poprawna
                CR_flag = 0  # Wyzerowanie flagi
#                 readFrameData(Addr) # Addr, Data # W tym przypadku watek checkFrame czeka niepotrzebnie? na wykonanie wywolanej funkcji - wprowadzenie zmiennej globalnej i przerwania od zmiany wartosci zmiennej?
                Data = ""
            else:
                checksum = -1 # Ramka nieprawidlowa
                print(str(Addr) + " | Ramka nieprawidlowa - niepoprawna dlugosc ramki")
        else:
            checksum = -1 # Ramka nieprawidlowa
            print(str(Addr) + " | Ramka nieprawidlowa - brak CR")

        # Wyzeruj licznik ramki
        bitCnt = 0
        
        print(str(Addr) + " | " + str(checksum) + " | " + str(time.time() - startTime)) # Czas odbioru ramki [s] ?
        print(tine.time() - startTime)

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
            print(str(SR2hex) + " - niepoprawny znak")
            
        else:  # Znaki poprawne -> dalsza analiza ramki

            # Polacz znaki w byte
            bitCnt += 1
            if bitCnt > 6:
                merge2word(A) # Lączenie danych/slow | Prosta forma | W razie potrzeby mozna przygotowac rozpoznawanie ilosci slow
            else:
                merge2byte(A) # Laczenie bajtow w dwuznakowy HEX

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
                
    return checksum;


while True:
    if bitCnt == 0:
        startTime = time.time()
    # Odbierz byte z buforu
    SR = SerialData.read()
    
    # Konwersja
    SR2hex = SR.hex()
    SR2int = int(SR2hex, 16)

    # Funkcja rozpoznania ramki
    checkFrame(SR2int)

