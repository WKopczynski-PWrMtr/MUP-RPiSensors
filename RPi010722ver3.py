# WKopczynski 2022
# Projekt zaliczeniowy MUP, PWr 2022
# 

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
import random



time1 = startTime = perf_counter()

#################################################
### Zmienne globalne - modyfikacja parametrow ###
#################################################
czasZapisuTxtT1 = 1   # Zakres 60-600s
czasZapisuTxtT2 = 1   # Zakres 10-120min
czasZapisuTxtT3 = 1   # Zakres 1-1440min
numbOfMasters = 11    # Ilosc podlaczonych urzadzen nadawczych

#################################################

#################################################
###       Wizualizacja linii pomiarowych      ###
###     W celu podgladu danych z czujnika     ###
###              ustawic wartosc 1            ###
#################################################
vis_T1 = 0      # Czujnik temperatury T1
vis_T2 = 0      # Czujnik temperatury T2
vis_T3 = 0      # Czujnik temperatury T3
vis_ADC1 = 0    # Przetwornik ADC1
vis_RTC = 1     # Zegar RTC
vis_F1 = 0      # Belka tensometryczna NA27
vis_F2 = 0      # Przetwornik SparkFun HX711
vis_WDS = 0     # Czujnik WDS-1000
vis_CPR = 0     # Czujnik CPR240
vis_SHARP30 = 0 # Czujnik odleglosci SHARP30
vis_SR04 = 0    # Czujnik odleglosci HC-SR04

#################################################


### Zmienne globalne
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
SR = b''
char = b''
fram = ""
inactiveUARTflag = 0
flagSave2LOG = 0
flagSave2TXT = 0
flagSave2SRV = 0
strBuffer = b''
strBuffer2 = b''
stopRec = 0

# Parametry czasowe
T1 = 10#czasZapisuTxtT1 # 60-600s
T2 = 20#60 * czasZapisuTxtT2 # 10-120min -> 600-7200s
T3 = 30#60 * czasZapisuTxtT3 # 1-1440min -> 60-86400s
timer = 0
noDataStartTime = 0


# Dane pomiarowe z ustalonych okresow Tx | Dost??p dla podprogramu | Zerowanie przy przerwaniach czasowych okreslonym okresami T
termAT1 = []
termBT1 = []
termCT1 = []
ADC1T1 = []
RTCT1 = []
F1T1 = []
F2T1 = []
WDST1 = []
CPRT1 = []
SHARP30T1 = []
SR04T1 = []
TESTT1 = []

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


# 
TempLists = [termAT1, termBT1, termCT1, ADC1T1, RTCT1, F1T1, F2T1, WDST1, CPRT1, SHARP30T1, SR04T1]
mergedDataT1 = [termAdd, termBdd, termCdd, ADC1dd, RTCdd, F1dd, F2dd, WDSdd, CPRdd, SHARP30dd, SR04dd]
mNames = ["Termometr A", "Termometr B", "Termometr C", "ADC1", "RTC", "F1", "F2", "WDS", "CPR", "SHARP30", "SR04"]
mValues = ["[*C]", "[*C]", "[*C]", "[]", "[]", "[dN]", "[dN]", "[mm]", "[mm]", "[mm]", "[cm]"]


##################### Inicjalizacja programu #####################
# Inicjalizacja portu ttyNVT0
call('sudo ttynvt -M 199 -m 6 -n ttyNVT0 -S 156.17.14.245:22029', shell=True)
sleep(0.1)

# Inicjalizacja po????czenia z serwerem port??w
SerialData = serial.Serial("/dev/ttyNVT0",115200)




##################### Funkcje - zapis do plikow #####################

## Zapis do pliku dziennego LOG (Watek glowny | T1) ##
def save2LOG():
    global mergedDataT1, mNames, mValues
    
    # Format: [Czas systemowy zapisu] [Kategoria komunikatu] [Dane]
    Log_Format = "%(asctime)s %(levelname)s %(message)s"
    
    logging.basicConfig(filename = "RPi " + str(datetime.datetime.now()),
                        filemode = "w",
                        format = Log_Format,
                        level = logging.INFO)
    logger = logging.getLogger()
    
    for x in range(11):
        logger.info([mNames[x], mValues[x], mergedDataT1[x]]) 


## Zapis odebranych danych do RAM (Watek 2) ##       XXXXXXXXXXXXXXXXXX
def save2RAM(data):
    global fram
    
    fram = open("/mnt/ramdisk/RPiTempData.txt", "a") # (append) Otworzenie pliku z podanej sciezki lub jego utworzenie, jesli nie istnieje. Zapis nowych danych na koncu pliku
#     print(data)
#     sleep(1)
    try:
        data2 = data.decode("utf-8")
    except ValueError:
        fram.close()
    else:
        fram.write(str(data2))
        fram.close()
#     return


## Zapis danych z RAM do SD w formacie TXT (Watek glowny | T2) ##
def save2TXT():       #XXXXXXXXXXXXXXXXXX
    global fram
    
#     fram.close()
    # Przeniesienie pliku z danymi RAM -> SD (katalog /home/pi)
    call('mv /mnt/ramdisk/RPiTempData.txt /home/pi/RPiTempData.txt', shell=True)
    # Ustalene nazwy pliku w momencie jego zamkniecia
    fname = "RPi" + str(datetime.datetime.now()) + ".txt"
    # Zaktualizowanie nazwy pliku (mozliwa rowniez zmiana nazwy przy komendzie mv)
    os.rename("/home/pi/RPiTempData.txt", "/home/pi/" + fname)
    # Otworzenie nowego pliku zapisu w RAM
#     fram = open("/mnt/ramdisk/RPiTempData.txt", "a") # (append) Otworzenie pliku z podanej sciezki lub jego utworzenie, jesli nie istnieje. Zapis nowych danych na koncu pliku
      

##################### Funkcje - ramka danych #####################
### Analiza danych z ramki cd (Watek 2) ###
def readFrameData(adress):
    global start, Data, bitCnt, termAT1, termBT1, termCT1, ADC1T1, RTCT1, F1T1, F2T1, WDST1, CPRT1, SHARP30T1, SR04T1, TempLists, mergedDataT1, vis_T1, vis_T2, vis_T3, vis_ADC1, vis_RTC, vis_F1, vis_F2, vis_WDS, vis_CPR, vis_SHARP30, vis_SR04
 
#     print(Data)
#
    # Termometr A
    if adress == '01': # DS18B20 | 1bit = 0,0625*C | Zakres: (-50) ... (+125) | FC90 - 07D0 (HEX) | Rozdzielczo???? 1K
         # str > int > obliczenie wartosci: 0,0625*C na bin
        pomiar = int(Data,16) * 0.0625
        termAT1.append(pomiar)
        if vis_T1 == 1:
            print("Termometr A: " + str(round(pomiar)) + "*C")

#
    # Termometr B
    elif adress == '02': # Pt1000 | 1bit = ... | Zakres: 0...250 | Rozdzielczo???? 1K (max) | dane temp?# str > int > obliczenie wartosci: 1*C na bin
        if len(Data) < 5:
            pomiar = int(Data,16) * 1 # Do podmienienia przelicznik
            termBT1.append(pomiar)
            if vis_T2 == 1:
                print("Termometr B: " + str(round(pomiar)) + "*C")

#
    # Termometr C
    elif adress == '12': # LM35 | 1bit = ... | Zakres: 0...100 # str > int > obliczenie wartosci: 1*C na bin
        pomiar = int(Data,16) * 1 # Do podmienienia przelicznik
        termCT1.append(pomiar)
        if vis_T3 == 1:
            print("Termometr C: " + str(round(pomiar)) + "*C")
        
# 
    # WDS
    elif adress == '0C': # WDS-1000-MP-C3-P # str > int > obliczenie wartosci: 1x na bin
        pomiar = int(Data,16) * 1 # Do podmienienia przelicznik
        WDST1.append(pomiar)
        if vis_WDS == 1:
            print("WDS: " + str(round(pomiar)) + "mm")
        
# 
    # CPR
    elif adress == '08': # CPR240 # str > int > obliczenie wartosci: 1x na bin
        pomiar = int(Data,16) * 1 # Do podmienienia przelicznik
        CPRT1.append(pomiar)
        if vis_CPR == 1:
            print("CPR: " + str(round(pomiar)) + "mm")        
    
# 
    # SHARP30
#     elif adress == '0D': # GP2Y0A41SK0F # str > int > obliczenie wartosci: 1x na bin
        pomiar = int(Data,16) * 1 # Do podmienienia przelicznik
        SHARP30T1.append(pomiar)
        if vis_SHARP30 == 1:
            print("SHARP30: " + str(round(pomiar)) + "cm")  
#         return
    
# 
    # SR04
    elif adress == '0E': # HC-SR04 # str > int > obliczenie wartosci: 1x na bin
        pomiar = int(Data,16) * 1 # Do podmienienia przelicznik
        SR04T1.append(pomiar)
        if vis_SR04 == 1:
            print("SR04: " + str(round(pomiar)) + "cm")  
    
# 
    # F1
    elif adress == '06': # Belka tensometryczna NA27 | podaje warto??????redni?? W | brak WL WH | # str > int > obliczenie wartosci: 1x na bin
        pomiar = int(Data,16) * 1 # Do podmienienia przelicznik
        F1T1.append(pomiar)
        if vis_F1 == 1:
            print("F1: " + str(round(pomiar)) + "dN")  
    
# 
    # F2
    elif adress == '07': # SparkFun HX711 # str > int > obliczenie wartosci: 1x na bin
        pomiar = int(Data,16) * 1 # Do podmienienia przelicznik
        F2T1.append(pomiar)
        if vis_F2 == 1:
            print("F2: " + str(round(pomiar)) + "dN")  
    
# 
    # RTC
    elif adress == '05':
        yr=Data[0:2]
        mt=Data[2:4]
        dy=Data[4:6]
        hr=Data[6:8]
        mn=Data[8:10]
        sc=Data[10:12]
        pomiar2 = str(yr) + "/" + str(mt) + "/" + str(dy) + " " + str(hr) + ":" + str(mn) + ":" + str(sc)
        RTCT1.append(pomiar2)
        if vis_RTC == 1:
            print("RTC: " + pomiar2)
    
# 
    # ADC1
    elif adress == '03':
        for x in range(15):
            pomiarx = Data[4*x:4*x+4]
            if x == 15:
                pomiar3 += str(pomiarx)
            else:
                pomiar3 += str(pomiarx) + " "
        ADC1T1.append(pomiar3)
        if vis_ADC1 == 1:
            print(pomiar3)
    
#
    # Podlaczenie nieobslugiwanego urzadzenia
    else:
#         print(str(adress) + " | Podlaczono nieobslugiwane urzadzenie. Wymagana modyfikacja kodu.")
        return



### Ramka danych (Watek 2)###
def checkFrame(A):
    global Addr, LenD, ComL, MSB, LSB, FByte, bitCnt, CR_flag, checksum, Data, SR2hex, startTime, timeRecv
    timeRecv = perf_counter()
#     print(A)
    ## Znak /n
    if A == 10:
        # Sprawdz poprawnosc ramki (czy wystapil wczesniej znak CR)
        if CR_flag == 1:
            # Okreslenie prawidlowej dlugosci ramki (ilosc wyrazow * 4bity na wyraz + 6 bitow wiodacych + 2 bity koncowe + przesuniecie licznika w dol jako liczenie od zera)
#             print(LenD)
            frameLen = int(LenD,16)*4+6+2-1
            # Sprawdz czy ramka ma poprawna dlugosc
            if frameLen == bitCnt:
                if len(Data) == int(LenD,16)*4:
    #                 print("len: " +str(frameLen))
    #                 print("cnt: " +str(bitCnt))
                    checksum = 1 # Ramka poprawna
                    CR_flag = 0  # Wyzerowanie flagi
                    readFrameData(Addr) # Addr, Data # W tym przypadku watek checkFrame czeka niepotrzebnie? na wykonanie wywolanej funkcji - wprowadzenie zmiennej globalnej i przerwania od zmiany wartosci zmiennej?
                else:
                    checksum = -1
#                     print("Nieprawidlowa ilosc danych")
                Data = ""
#                 print("Ramka ok")
#                 print(perf_counter() - timeRecv)
            else:
                checksum = -1 # Ramka nieprawidlowa
#                 print(str(Addr) + " | Ramka nieprawidlowa - niepoprawna dlugosc ramki")
        else:
            checksum = -1 # Ramka nieprawidlowa
#             print(str(Addr) + " | Ramka nieprawidlowa - brak CR")

        # Wyzeruj licznik ramki
        bitCnt = 0

    # Znak /r
    elif A == 13:
        # Aktywuj flage, zwieksz licznik
        if (bitCnt - 6) % 4 == 0: # Sprawdzenie czy ramka posiada poprawna ilosc wyrazow (
            CR_flag = 1
            bitCnt += 1
        else:
            checksum = -1
#             print(str(Addr) + " | Ramka nieprawidlowa - niepoprawna dlugosc danych ramki przed znakiem CR")

    # Pozostale elementy ramki
    else:
        # Sprawdz poprawnosc znakow (czy sa HEXami)
        A -= 48 # Czy sa to znaki 0-9
        if A > 16:
            A -= 7 # Czy sa to znaki A-F
        if A > 16: # Jesli nadal poza zakresem -> nie sa HEXem
            checksum = -1 # Ramka nieprawidlowa
#             print(str(A) + " | Ramka nieprawidlowa - znak nie nalezy do HEX")
        else:  # Znaki poprawne -> dalsza analiza ramki
            # Polacz znaki
            bitCnt += 1
            if bitCnt > 6: # Laczenie bajtow w dane
                Data += str(int2hex(A,4)[2:3])
#                 print(int2hex(A,4)[2:3])
#                 print(Data)
            else: # Laczenie bajtow w dwuznakowy HEX
                if bitCnt % 2 == 1:
                    MSB = int2hex(A,4)
                else:
                    LSB = int2hex(A,4)
                    FByte = str(MSB[2:]) + str(LSB[2:])
#                     print(FByte)
            
            # Sprawdzenie pol analizowanej ramki
            # Adres
            if bitCnt == 2:
                Addr = FByte
#                 print(Addr)

            # Dlugosc ramki
            elif bitCnt == 4:
                LenD = FByte
#                 print("LenD: " + str(LenD))

            # ComL
            elif bitCnt == 6:
                ComL = FByte
                if hex2int(ComL,8) != (0 - hex2int(LenD,8)): # Sprawdzenie liczby kontrolnej (ComL = 00h - LenD)
                    checksum = -1
#                     print(str(Addr) + " | Ramka nieprawidlowa - brak zgodnosci LenD <> ComL")
#                 print(ComL)


def int2hex(val, nbits): # Przelicz int na hex (ze znakami ujemnymi)
  return hex((val + (1 << nbits)) % (1 << nbits)).upper()

def hex2int(val, nbits): # Przelicz hex na int (ze znakami ujemnymi)
  return int(val, 16) - ((int(val, 16) >> 7) * 256)


##################### Watki rownolegle #####################
def USARTctrl(): # Odbior danych z USART (Watek 1)
    global SR, strBuffer
    
    while True:
#         start2 = perf_counter()
        if SerialData.inWaiting() > 0 and stopRec == 0: # Odbior zablokowany w momencie kopiowania buforu w drugim watku
            SR = SerialData.read(SerialData.inWaiting()) # Pobor calej dostepnej paczki danych | szybsza obrobka, zwolnienie miejsca w buforze pySerial (ograniczony do 4095)
#             timeSR = perf_counter() - startTime
            strBuffer += SR
#         print(perf_counter()-start2)
#         print(strBuffer)


def USARTbuffer(): # Buforowanie danych (Watek 2)
    global strBuffer, strBuffer2, stopRec, noDataStartTime, char
    cnt = 0
    SR2int = -1
    while True:
#         start3 = perf_counter()
        if len(strBuffer) > 0:
            stopRec = 1 # Zabezpieczenie przed odbiorem danych z USART w momencie kopiowania buforu
            strBuffer2 += strBuffer # Zabezpieczenie przed nadpisaniem buforu w wielowatkowej pracy
            strBuffer = b'' # Zwolnienie buforu z drugiego watku
#         print(strBuffer2)
            
        # Pobranie znaku (FIFO)
        char = strBuffer2[0:1]
        save2RAM(char)
        strBuffer2 = strBuffer2[1:len(strBuffer2)] # Usuniecie pobranego znaku z pozostalych danych
        stopRec = 0 # Zdjecie blokady pobierania danych z USART
        
        # Konwersja bajt -> hex -> int
#         SR2str = char.decode("utf-8")
#         SR2str = str(char)
#         SR2hex = char.hex()
        SR2int = int.from_bytes(char, 'big')
#         SR2int = int(SR2hex,16)
#         print("char: " + str(char))
#         print("A: " + str(SR2int))
#         print("Buf: " + str(strBuffer2))
        if len(char) == 0:
            SR2int = -1
        else:
#             print(char)
            checkFrame(SR2int) # Uruchomienie analizy ramki

        # Oznaczenie braku danych do odczytu (dot. zadania T3)
        if len(strBuffer2) == 0:
            if noDataStartTime == 0: # Gdy bufor ulegl dopiero zwolnieniu
                noDataStartTime = perf_counter() # Zapis czasu zwolnienia buforu
        else:
            noDataStartTime = 0 # Wyzerowanie czasu w momencie wykrycia danych
            
        # Zapisanie nowopobranego znaku do pliku w pamieci RAM (dot. T2)
#         char = b''
#         print(perf_counter()-start3)


## Stoper ##                                                          >> OK
def stoper(): # Stoper + aktywacje flag dla okresow T1, T2, T3 (Watek 3)
    global timer, T2, T1, T3, strBuffer2, noDataStartTime, flagSave2LOG, flagSave2TXT, flagSave2SRV
    
    while True:
        startTime = perf_counter() #perf_counter()
        timer += 1
        
        if timer % T1 == 0: # Aktywowanie flagi w czasie T1
            flagSave2LOG = 1
#             print("log")
            
        if timer % T2 == 0: # Aktywowanie flagi w czasie T2
            flagSave2TXT = 1
#             print("txt")
            
        if (math.floor(perf_counter() - noDataStartTime) % 10 == 0 and len(strBuffer2) > 0) or timer % T3 == 0: # Aktywowanie flagi w czasie T3 lub w przypadku braku danych do odczytu w czasie 10s
            flagSave2SRV = 1
#             print("srv")
            
        sleep(1 - (perf_counter() - startTime))
#         print(timer)


# Uruchomienie watku z odbiorem danych USART
USART_thread = threading.Thread(target = USARTctrl)
USART_thread.start()

#Uruchomienie watku z buforem danych
USARTbuffer_thread = threading.Thread(target = USARTbuffer)
USARTbuffer_thread.start()

#Uruchomienie watku z buforem danych
Timer_thread = threading.Thread(target = stoper)
Timer_thread.start()

### Petla glowna (Watek glowny) ###
while True:
#     start2 = perf_counter()
    
    # save2LOG | Okresowy zapis wartosci srednich z czasie T1 do przebiegu dziennego
    if flagSave2LOG == 1:
        flagSave2LOG = 0 # Zwolnienie flagi, rozpoczecie procedury
        for h in range(numbOfMasters):
            if len(TempLists[h]) > 0: # Zapis, jesli dany array nie jest pusty
                if h == 4: # warunek dla RTC
                    pass
                else:
                    # Wyznacz wartosc srednia z danych mastera odebranych w okresie T1 oraz ich wartosc maksymalna i minimalna, zgraj do tablic T2, oczysc tablice T1
                    val = round(sum(TempLists[h])/len(TempLists[h]))
                    valMin = round(min(TempLists[h]))
                    valMax = round(max(TempLists[h]))
                    mergedDataT1[h].append([val,valMin,valMax]) # Forma zapisu w tablicy pomiarow: [wart. srednia, wart. minimalna, wart. maksymalna]
                    print(mNames[h] + " |   Av: " + str(val) + str(mValues[h]) + "  Min: " + str(valMin) + str(mValues[h]) + "  Max: " + str(valMax) + str(mValues[h]))
                    TempLists[h] *= 0
                # Wizualizacja danych co okres T1
                
        save2LOG();

    # save2TXT | Okresowy zapis wszystkich odebranych danych w czasie T2 do pliku TXT na SD lub po czasie 10s, gdy brak danych do zapisu
    if flagSave2TXT == 1:
        flagSave2TXT = 0 # Zwolnienie flagi, rozpoczecie procedury
        save2TXT();
    
    # save2SRV | Zapis na serwer ...
    if flagSave2SRV == 1:
        flagSave2SRV = 0 # Zwolnienie flagi, rozpoczecie procedury
        # Ustanowienie/odnowienie polaczenia zwrotnego z serwerem (brak publicznego IP rejestratora)



#     print(perf_counter()-start2)




