# WKopczynski 2022
# Projekt zaliczeniowy MUP, PWr 2022
# Cz1 - odbior danych UART na RPi4B


# Odbior i przetwarzanie kodu (bajtow) odebranych przez UART/siec z magistrali
# RS485. Okres aktualizacji nie wiekszy niz Ts=125ms.


# 1. Odbior danych przez UART
# 2. Weryfikacja poprawnosci znakow ramki danych
# 3. Przetwarzanie danych pobranych z ramki
# 4. Cykliczna obsluga urzadzenia do wizualizacji


# Urzadzenia typu master na magistrali RS485
# |Adres|    Nazwa    | sl/zn |  us  |
# | 01h | termometr A |  1/12 | 1041 |
# | 02h | termometr B |  1/12 | 1041 |
# | 12h | termometr C |  1/12 | 1041 |
# | 03h |    ADC1     | 16/72 | 6250 |
# | 05h |     RTC     |  3/30 | 1736 |
# | 06h |      F1     |  2/16 | 1388 |
# | 07h |      F2     |  2/16 | 1388 |
# | 0Ch |     WDS     |  1/12 | 1041 |
# | 08h |     CPR     |  1/12 | 1041 |
# | 0Dh |   SHARP30   |  1/12 | 1041 |
# | 0Eh |    SR04     |  1/12 | 1041 |


# ttyS0 - miniUART
# ttyAMA0 - PL011 UART
# ttyNVT0 - polaczenie internetowe / dziala jako port szeregowy

#sudo ttynvt -D 9 -M 199 -m 6 -n ttyNVT0 -S 156.17.14.245:22029

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


##################### Zmienne globalne, tablice #####################
### Zmienne globalne
#MUPsettings.init()
Addr = ""      # Adres mastera
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

# Dane pomiarowe z ustalonych okresow Tx | Dostęp dla podprogramu | Zerowanie przy przerwaniach czasowych okreslonym okresami T
termAtd = []
termBtd = []
termCtd = []
ADC1td = []
RTCtd = []
F1td = []
F2td = []
WDStd = []
CPRtd = []
SHARP30td = []
SR04td = []
TESTtd = []

# Dane pomiarowe (wartosci srednie z okresu T1) z danego dnia pracy programu
termAdd = []
termBdd = []
termCdd = []
ADC1dd = []
RTCdd = []
F1dd = []
F2dd = []
WDSdd = []
CPRdd = []
SHARP30dd = []
SR04dd = []
TESTdd = []

DailyDataMerged = ["Termometr A", "Termometr B", "Termometr C", "ADC1", "RTC", "F1", "F2", "WDS", "CPR", "SHARP30", "SR04"]

# Skrotowce
TempLists = [termAtd, termBtd, termCtd, ADC1td, RTCtd, F1td, F2td, WDStd, CPRtd, SHARP30td, SR04td]
DailyData = [termAdd, termBdd, termCdd, ADC1dd, RTCdd, F1dd, F2dd, WDSdd, CPRdd, SHARP30dd, SR04dd]
mNames = ["Termometr A", "Termometr B", "Termometr C", "ADC1", "RTC", "F1", "F2", "WDS", "CPR", "SHARP30", "SR04"]
mValues = ["T[*C]", "T[*C]", "T[*C]", "[]", "[]", "[dN]", "[dN]", "[mm]", "[mm]", "[mm]", "[cm]"]

##################### Inicjalizacja programu #####################
# Inicjalizacja portu ttyNVT0
call('sudo ttynvt -M 199 -m 6 -n ttyNVT0 -S 156.17.14.245:22029', shell=True)
sleep(0.1)
# Tworzenie wirtualnego RAM do tymczasowego zapisu danych pomiarowych
# call('sudo mount ramfs /ram -t ramfs -o size=16M') #
# fram = open("/mnt/ramdisk/RPiTempData.txt", "a") # (append) Otworzenie pliku z podanej sciezki lub jego utworzenie, jesli nie istnieje. Zapis nowych danych na koncu pliku

# Inicjalizacja połączenia z serwerem portów
SerialData = serial.Serial("/dev/ttyNVT0",115200)
    #port = 'COM3',
    #baudrate = 115200#,
    #bytesize = serial.EIGHTBITS,
    #parity = serial.PARITY_NONE,
    #stopbits = serial.STOPBITS_ONE


##################### Watki rownolegle #####################
### Odbior danych z USART ###
def USARTctrl():
    global SR, SR2hex, SR2int, bitCnt, startTime, timeRecv, noDataTimer, inactiveUARTflag
    
    while True:
        if bitCnt == 0:
            startTime = time.time()
        # Odbierz byte z buforu
        SR = SerialData.read()
        if SR:
            timeRecv = perf_counter()
            noDataTimer = 0
            save2RAM(SR)
        elif timeRecv > 0: # Sprawdzenie timera, gdy zarejestrowano wczesniej dane
            noDataTimer = perf_counter() - timeRecv
            if noDataTimer >= 10:
                inactiveUARTflag = 1
            timeRecv = 0

        # Konwersja
        SR2hex = SR.hex()
        SR2int = int(SR2hex, 16)

        # Funkcja rozpoznania ramki
        checkFrame(SR2int)

## Stoper ##                                                          >> OK
def stoper():
    global timer, T2, T1, timer_flag, timer_flag2
    
    while True:
        for x in range(T2):
            startTime = time.time() #perf_counter()
            timer += 1
            timer_flag = timer
            timer_flag2 = timer
            sleep(1 - (time.time() - startTime))
            
            print(x)
        

##################### Funkcje - zapis do plikow #####################

## Zapis do pliku dziennego LOG ##
def save2LOG():
    global DailyDataMerged, DailyData, mNames, mValues
    
    # Format: [Czas systemowy zapisu] [Kategoria komunikatu] [Dane]
    Log_Format = "%(asctime)s %(levelname)s %(message)s"
    
    logging.basicConfig(filename = "RPi " + str(datetime.datetime.now()),
                        filemode = "w",
                        format = Log_Format,
                        level = logging.INFO)
    logger = logging.getLogger()
    
    for x in range(11):
        logger.info([mNames[x], mValues[x], DailyData[x]]) 



## Zapis odebranych danych do RAM ##       XXXXXXXXXXXXXXXXXX
def save2RAM(data):
    global fram
    
    fram = open("/mnt/ramdisk/RPiTempData.txt", "a") # (append) Otworzenie pliku z podanej sciezki lub jego utworzenie, jesli nie istnieje. Zapis nowych danych na koncu pliku
    data2 = data.decode("ascii")
    fram.write(str(data2))
    fram.close()
#     return



def save2TXT():       #XXXXXXXXXXXXXXXXXX
    global fram
    
#     fram.close()
    # Przeniesienie pliku z danymi RAM -> SD (katalog /home/pi)
    call('mv /mnt/ramdisk/RPiTempData.txt /home/pi/RPiTempData.txt', shell=True)
    # Ustalene nazwy pliku w momencie jego zamkniecia
    fname = "RPiTest" + str(datetime.datetime.now()) + ".txt"
    # Zaktualizowanie nazwy pliku (mozliwa rowniez zmiana nazwy przy komendzie mv)
    os.rename("/home/pi/RPiTempData.txt", "/home/pi/" + fname)
    # Otworzenie nowego pliku zapisu w RAM
#     fram = open("/mnt/ramdisk/RPiTempData.txt", "a") # (append) Otworzenie pliku z podanej sciezki lub jego utworzenie, jesli nie istnieje. Zapis nowych danych na koncu pliku
      
    # Zapis danych na dysk wirtualny
    # Zapis danych z wirtualnego dysku na karte SD w formie pliku TXT
    # po okreslonym czasie lub przy braku nowych danych w okreslonym odstepie czasowym
    return
    


##################### Funkcje - obrobka danych z USART #####################

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
        
#         print(str(Addr) + " | " + str(checksum) + " | " + str(time.time() - startTime)) # Czas odbioru ramki [s] ?

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



### Analiza danych z ramki ###

def readNormalFrame(data):
    data2hex = data.hex()
    data2int = int(data2hex, 16)
    return data2int



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
        print(Data)
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

    return;




##################### Program glowny #####################
### Wlaczenie wielowatkowosci
#> Odbior danych z USART
USART_thread = threading.Thread(target = USARTctrl)
USART_thread.start()

# Stoper
stoper_thread = threading.Thread(target = stoper)
stoper_thread.start()



### PETLA GLOWNA ###
while True:
    
    # save2LOG | Okresowy zapis wartosci srednich z czasie T1 do przebiegu dziennego
    start2 = time.time()
    
    if (timer_flag + 1) % T1 == 0: # Sprawdzic przypadek, gdy krotnosc T1 pokrywa sie z T2
        
#         timer_flag2 = timer_flag
        timer_flag = 0
        
        print("T1 - wyznaczenie wartosci sredniej")
#         print(Temptd.min()[2])
        for h in range(11):
            if len(TempLists[h]) > 0:
                # [termAtd, termBtd, termCtd, ADC1td, RTCtd, F1td, F2td, WDStd, CPRtd, SHARP30td, SR04td]

                # Wyznacz wartosc srednia z danych mastera odebranych w okresie T1 oraz ich wartosc maksymalna i minimalna, zgraj do tablic T2, oczysc tablice T1
                val = sum(TempLists[h])/len(TempLists[h])
                valMin = min(TempLists[h])
                valMax = max(TempLists[h])
                print(DailyDataMerged[h] + " |   Av: " + str(val) + "  Min: " + str(valMin) + "  Max: " + str(valMax))
                DailyData[h].append([val,valMin,valMax]) # Dodac wartosci min i max
                TempLists[h] *= 0
        

    # save2RAM | Okresowy zapis wszystkich odebranych danych w czasie T2 do pliku TXT na SD lab po czasie 10, gdy brak danych na linii
    if (timer_flag + 1) % T2 == 0 or (timer_flag + 1) % 10 == 0 or (timer_flag2 + 1) % T2 == 0 or (timer_flag2 + 1) % 10 == 0 or noDataTimer >= 10 or inactiveUARTflag == 1:
        timer_flag = 0
        timer_flag2 = 0
        inactiveUARTflag = 0
        
        save2TXT();
        save2LOG();
        print("T2 - zgranie plikow do pliku dziennego LOG")
        for i in range(11):
            DailyData[i] *= 0 # Czyszczenie danych
            
         
