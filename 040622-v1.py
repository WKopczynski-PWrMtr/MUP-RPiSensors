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

import sys
import math
import struct
import numpy as np
from subprocess import call
import serial # https://pyserial.readthedocs.io/en/latest/pyserial_api.html
from time import sleep
import time


### Zmienne globalne
Addr = ""     # Adres mastera
LenD = 00      # Dlugosc ramki
Coml = 00      # Dopelnienie LenD
MSB = 0000       # msb
LSB = 0000       # lsb
FByte = ''  # msb + lsb
bitCnt = 0    # Licznik dlugosci ramki
CR_flag = 0   # Flaga znaku '\r'
checksum = 0  # Poprawnosc odebranej ramki
Addr = "12"
WH = ''
WL = ''
WRD = ''

T1 = 60 # 60-600s
T2 = 0

# Dane pomiarowe z ustalonych okresow Tx | Dostęp dla podprogramu | Zerowanie przy przerwaniach czasowych okreslonym okresami T
termAList = []
termBList = []
termCList = []
ADC1List = []
RTCList = []
F1List = []
F2List = []
WDSList = []
CPRList = []
SHARP30List = []
SR04List = []


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


### Skladanie bajtu ###
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
def merge2word(B):
    global Data, FByte

    Data += FByte

    """global FByte, bitCnt, WH, WL, WRD

    if (bitCnt - 6) % 4 == 1:
        WH = FByte
    else:
        WL = FByte
        WRD = WH + WL
    """

    return;


### Odczyt ramki ###
def checkFrame(A):
    global Addr, LenD, ComL,MSB, LSB, FByte, bitCnt, CR_flag, checksum
#     print(A)
    ## Znak /n
    if A == 10:

        # Sprawdz poprawnosc ramki (czy wystapil wczesniej znak CR)
        if CR_flag == 1:
            checksum = 1 # Ramka poprawna
            CR_flag = 0  # Wyzerowanie flagi
            readFrameData() # Addr, Data
        else:
            checksum = -1 # Ramka nieprawidlowa

        # Wyzeruj licznik ramki
        bitCnt = 0

    # Znak /r
    elif A == 13:

        # Aktywuj flage, zwieksz licznik
        CR_flag = 1
        bitCnt += 1

    # Pozostale elementy ramki
    else:

        # Sprawdz poprawnosc znakow (czy sa HEXami)
        A -= 48 # Czy sa to znaki 0-9
        if A > 16:
            A -= 7 # Czy sa to znaki A-F
        if A > 16: # Jesli nadal poza zakresem -> nie sa HEXem
            checksum = -1 # Ramka nieprawidlowa
        else:

            # Znaki poprawne -> dalsza analiza ramki

            # Polacz znaki w byte
            bitCnt += 1
            if bitCnt > 6:
                merge2word(A) # Lączenie danych/slow | Prosta forma | W razie potrzeby mozna przygotowac rozpoznawanie ilosci slow
            else:
                merge2byte(A) # Laczenie bajtow w dwuznakowy HEX
#             print(bitCnt)

            ## Sprawdz byte

            # Adres
            if bitCnt == 2:
                Addr = FByte
                readFrameData(Addr)
#                 print(Addr)

            # Dlugosc ramki
            elif bitCnt == 4:
                LenD = FByte

            # ComL
            elif bitCnt == 6:
                ComL = FByte
#                 tabb = "\t"
#                 print("Addr: " + str(Addr) + tabb + "LenD: " + str(LenD) + tabb + "ComL: " + str(ComL))

            # Pozostale dame
            elif bitCnt > 6:
#                 merge2word(A)
                # Utworz tablice danych
                return

#     print(bitCnt)
    return checksum;


### Analiza danych z ramki ###

def readNormalFrame(data):


    return

### Analiza danych z ramki cd ###
def readFrameData():
    global Addr, Data, bitCnt, termAList, termBList, termCList, ADC1List, RTCList, F1List, F2List, WDSList, CPRList, SHARP30List, SR04List

    # Termometr A
    if Addr == '01': # DS18B20 | 1bit = 0,0625*C | Zakres: (-50) ... (+125) | FC90 - 07D0 (HEX) | Rozdzielczość 1K
        # Mozna dodac obsluge bledow - sprawdzenie czy dane mieszcza sie w zakresie | z drugiej strony uzytkownik sam moze okreslic czy dany pomiar jest prawidlowy - moze to swiadczyc o problemie z czujnikiem

        str2int = int(data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
        # DO ZROBIENIA - Wyznaczenie wartosci ujemnych
        pomiar = str2int * 0.0625

        termAList.append(pomiar)
        print(Addr)

        # Wyznacz wartosc z danych
            # Zapisz czas odbioru?
        # Dodaj wartosc do listy (maks. ilosc elementow ograniczona do czasu T1) # Lista odbierana w podprogramie do wizualizacji danych
            # Wyznacz wartosc srednia z danych z listy
            # Wyznacz zakres danych - odczyt wartosci najnizszej i najwyzszej
            # Wizualizacja danych dla okreslonego okresu T1
            # Okreslenie daty zapisu
            # Zapis danych do pliku LOG z data w nazwie


    # Termometr B
    elif Addr == '02': # Pt1000 | 1bit = ... | Zakres: 0...250 | Rozdzielczość 1K (max) | dane temp?
        str2int = int(data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        termBList.append(pomiar)
        print(Addr)

    # Termometr C
    elif Addr == '12': # LM35 | 1bit = ... | Zakres: 0...100
        str2int = int(data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        termCList.append(pomiar)
        print(Addr)

    # WDS
    elif Addr == '0C': # WDS-1000-MP-C3-P
        str2int = int(data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        WDSList.append(pomiar)
        print(Addr)

    # CPR
    elif Addr == '08': # CPR240
        str2int = int(data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        CPRList.append(pomiar)
        print(Addr)

    # SHARP30
    elif Addr == '0D': # GP2Y0A41SK0F
        str2int = int(data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        SHARP30List.append(pomiar)
        print(Addr)

    # SR04
    elif Addr == '0E': # HC-SR04
        str2int = int(data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        SR04List.append(pomiar)
        print(Addr)

    # F1
    elif Addr == '06': # Belka tensometryczna NA27 | podaje wartośćśrednią W | brak WL WH | 
        print(Addr)

    # F2
    elif Addr == '07': # SparkFun HX711
        print(Addr)

    # RTC
    elif Addr == '05':
        print(Addr)

    # ADC1
    elif Addr == '03':
        print(Addr)

    # Zabezpieczenie przed bledami
    else:
#         print(str(Addr) + " #")
        return

    return;


### PETLA GLOWNA
while True:
#     start = time.time()
#     bytesToRead = SerialData.inWaiting()

    # Odbierz byte z buforu
    SR = SerialData.read()

    # Konwersja
#     asc = SR.decode("ascii")
    SR2hex = SR.hex()
#     print(SR2hex)
    SR2int = int(SR2hex, 16)
#     SR2bin = format(SR2int, '08b')

    # Podglad otrzymywanych znakow: str|int|hex|bin
#     tab = "\t"
#     print(f"{str(SR) + tab + str(SR2int) + tab + str(SR2hex) + tab + str(SR2bin)}")

    # Funkcja rozpoznania ramki
    checkFrame(SR2int)
#     readFrameData(Addr)
#     loopend = (time.time() - start)
#     print(loopend)
#     print(Addr)
#     if checksum != 1:
#         print(checksum)


    #sleep(.5)
    #if SR2int == 10:
#     print(SR)

#     print(bytesToRead)
#     if bytesToRead > 0:
#         print(SR)
    # SR = SerialData=read_until(expected=LF, size=NONE)
    # https://pyserial.readthedocs.io/en/latest/shortintro.html?highlight=readline#readline
    """
    match _char:
        case '/n':
            # return/break/exit()?
        case '/r':

        case _:
      """      

"""

if A == 10:
    Lenf = 1
elif A == 13:
    if Lenf == 1:
        Lenf = 2
    else:
        Lenf = 0
else:
    A -= 48
    if A > 16:
        A -= 7
    if A < 16:
        Lenf += 1
        if (Lenf << 1) == 0: # ???
            ...
"""
"""
global Lenf, B2

    if B == 10: # Sprawdz czy odebrany znak jest LF ('\n')
        Lenf = 1
    elif B == 13: # Sprawdz czy odebrany znak jest CR ('\r')
        Lenf = 2
    else: # Wykonaj instrukcje dla pozostalych znakow
        B -= 48 # HEX -> halfbyte (0-15)
        if B > 16:
            B -= 7
        if B < 16: # Sprawdz czy jest znakiem HEX
            Lenf += 1 # Ramka rosnie
            if Lenf % 2 == 0: # Sprawdz parzystosc numeru znaku (liczona od konca)
                B2 |= (B << 4) # Generowanie pelnego byte w HEX z przesunieciem MSB
                if Lenf == 12:
                    #

                    Lenf = 0
#                 else:
                    #
            else:
                B2 = B
                if Lenf > 12:
                    Lenf = 0

#                 struct.unpack("<I", struct.pack(">I", B))[0]
"""
