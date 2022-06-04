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

import numpy as np
import math
import matplotlib
import matplotlib.pyplot as plt
import serial # https://pyserial.readthedocs.io/en/latest/pyserial_api.html
import struct
from subprocess import call
import sys
import threading
import time
from time import sleep
import MUPsettings

##################### Zmienne globalne, tablice #####################
### Zmienne globalne
MUPsettings.init()
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

# Parametry czasowe # Ustawic w lepiej dostepnym miejscu do latwej zmiany parametrow
T1 = 3 # 60-600s
T2 = 30 # 10-120min -> 600-7200s
timer = 0

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
TESTList = []

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

# Skrotowce
TempLists = [termAList, termBList, termCList, ADC1List, RTCList, F1List, F2List, WDSList, CPRList, SHARP30List, SR04List]
DailyData = [termAdd, termBdd, termCdd, ADC1dd, RTCdd, F1dd, F2dd, WDSdd, CPRdd, SHARP30dd, SR04dd]


##################### Inicjalizacja programu #####################
# Inicjalizacja portu ttyNVT0
call('sudo ttynvt -M 199 -m 6 -n ttyNVT0 -S 156.17.14.245:22029', shell=True)
sleep(0.1)
# Tworzenie wirtualnego RAM do tymczasowego zapisu danych pomiarowych
# call('sudo mount ramfs /ram -t ramfs -o size=16M') # 

# Inicjalizacja połączenia z serwerem portów
SerialData = serial.Serial("/dev/ttyNVT0",115200)
    #port = 'COM3',
    #baudrate = 115200#,
    #bytesize = serial.EIGHTBITS,
    #parity = serial.PARITY_NONE,
    #stopbits = serial.STOPBITS_ONE

# Uruchomienie okna z przebiegami
x = np.linspace(0,1,timer)
y = termBdd
plt.ion()
fig = plt.figure()
ax = fig.add_subplot(111)
line1, = ax.plot(x,y,'r-')


##################### Funkcje #####################
### Stoper ###
def stoper():
    global T1, T2, timer, termBList, termBdd, TempLists, DailyData
    
    while True:
        
        for x in range(T2):
            
            # Okresowy zapis wartosci srednich z czasie T1 do przebiegu dziennego
            if (timer + 1) % T1 == 0: # Sprawdzic przypadek, gdy krotnosc T1 pokrywa sie z T2
                for h in range(11):
                    if len(TempLists[h]) > 0:
#                         print("TempList: ", str(TempLists[h]))
                        DailyData[h].append(sum(TempLists[h])/len(TempLists[h])) # Dodac wartosci min i max
                        line1.set_ydata(TempLists[h])
                        fig.canvas.draw()
                        fig.canvas.flush_events()
                        TempLists[h] *= 0
#                         print("TempList clr: ", str(TempLists[h]))
#                         print("DailyData: ", str(DailyData[h]))
#                     print(TempLists)
            # Okresowy zapis wszystkich odebranych danych w czasie T2 do pliku TXT na SD lab po czasie 10, gdy brak danych na linii
            if (timer + 1) % T2 == 0 or (timer + 1) % 10 == 0:
#                 print(DailyData)
                for i in range(11):
                    DailyData[i] *= 0 # Czyszczenie danych
                                    
            
            timer += 1 # Mozna zmienic na dokladniejsze liczenie czasu poprzez roznice czasu systemowego
            sleep(1)
            
            print(x)
            
#         print(TempLists)
        
# 
#         for i in TempLists:
#             i = []
#             print(i)
#         for j in DailyData:
#             print(j)
#         print(DailyData)
        print("####")
#         clearArrayPos_flag = 1
    


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
    global Data

    Data += SR.decode("ascii")

    return;


### Odczyt ramki ###
def checkFrame(A):
    global LenD, ComL,MSB, LSB, FByte, bitCnt, CR_flag, checksum, Data
#     print(A)
    ## Znak /n
    if A == 10:

        # Sprawdz poprawnosc ramki (czy wystapil wczesniej znak CR)
        if CR_flag == 1:
            checksum = 1 # Ramka poprawna
            CR_flag = 0  # Wyzerowanie flagi
            readFrameData() # MUPsettings.Addr, Data
            Data = ""
        else:
            checksum = -1 # Ramka nieprawidlowa

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
                MUPsettings.Addr = FByte
#                 readFrameData()
#                 print(MUPsettings.Addr)

            # Dlugosc ramki
            elif bitCnt == 4:
                LenD = FByte

            # ComL
            elif bitCnt == 6:
                ComL = FByte
#                 tabb = "\t"
#                 print("MUPsettings.Addr: " + str(MUPsettings.Addr) + tabb + "LenD: " + str(LenD) + tabb + "ComL: " + str(ComL))

            # Pozostale dame
#             elif bitCnt > 6:
#                 print(Data)
#                 merge2word(A)
                # Utworz tablice danych
#                 return

#     print(bitCnt)
    return checksum;


### Analiza danych z ramki ###

def readNormalFrame(data):


    return

### Analiza danych z ramki cd ###
def readFrameData():
    global start, Data, bitCnt, termAList, termBList, termCList, ADC1List, RTCList, F1List, F2List, WDSList, CPRList, SHARP30List, SR04List, TempLists, DailyData

    # TEST
    if MUPsettings.Addr == '14':
#         str2int = int(Data,16)
#         pomiar = str2int * 1 # Do podmienienia przelicznik
#         TESTList.append(pomiar)
#         print(TESTList)
#         print(MUPsettings.Addr)
        return
        

    # Termometr A
#     if MUPsettings.Addr == '01': # DS18B20 | 1bit = 0,0625*C | Zakres: (-50) ... (+125) | FC90 - 07D0 (HEX) | Rozdzielczość 1K
        # Mozna dodac obsluge bledow - sprawdzenie czy dane mieszcza sie w zakresie | z drugiej strony uzytkownik sam moze okreslic czy dany pomiar jest prawidlowy - moze to swiadczyc o problemie z czujnikiem

#         str2int = int(Data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
        # DO ZROBIENIA - Wyznaczenie wartosci ujemnych
#         pomiar = str2int * 0.0625

#         termAList.append(pomiar)
#         loopend = (time.time() - start)
#         print(loopend)
#         print(MUPsettings.Addr)
#         print(termAList)

        # Wyznacz wartosc z danych
            # Zapisz czas odbioru?
        # Dodaj wartosc do listy (maks. ilosc elementow ograniczona do czasu T1) # Lista odbierana w podprogramie do wizualizacji danych
            # Wyznacz wartosc srednia z danych z listy
            # Wyznacz zakres danych - odczyt wartosci najnizszej i najwyzszej
            # Wizualizacja danych dla okreslonego okresu T1
            # Okreslenie daty zapisu
            # Zapis danych do pliku LOG z data w nazwie


    # Termometr B
    elif MUPsettings.Addr == '02': # Pt1000 | 1bit = ... | Zakres: 0...250 | Rozdzielczość 1K (max) | dane temp?
        str2int = int(Data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        termBList.append(pomiar)
#         loopend = (time.time() - start)
#         print(loopend)
#         print(MUPsettings.Addr)
#         print(termBList)

    # Termometr C
    elif MUPsettings.Addr == '12': # LM35 | 1bit = ... | Zakres: 0...100
        str2int = int(Data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
        pomiar = str2int * 1 # Do podmienienia przelicznik
        termCList.append(pomiar)
#         print("# ", str(TempLists))
#         loopend = (time.time() - start)
#         print(loopend)
#         print(MUPsettings.Addr)
# 
#     # WDS
#     elif MUPsettings.Addr == '0C': # WDS-1000-MP-C3-P
#         str2int = int(Data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
#         pomiar = str2int * 1 # Do podmienienia przelicznik
#         WDSList.append(pomiar)
#         loopend = (time.time() - start)
#         print(loopend)
#         print(MUPsettings.Addr)
# 
#     # CPR
#     elif MUPsettings.Addr == '08': # CPR240
#         str2int = int(Data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
#         pomiar = str2int * 1 # Do podmienienia przelicznik
#         CPRList.append(pomiar)
#         loopend = (time.time() - start)
#         print(loopend)
#         print(MUPsettings.Addr)
# 
#     # SHARP30
#     elif MUPsettings.Addr == '0D': # GP2Y0A41SK0F
#         str2int = int(Data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
#         pomiar = str2int * 1 # Do podmienienia przelicznik
#         SHARP30List.append(pomiar)
#         loopend = (time.time() - start)
#         print(loopend)
#         print(MUPsettings.Addr)
# 
#     # SR04
#     elif MUPsettings.Addr == '0E': # HC-SR04
#         str2int = int(Data,16) # str > int > obliczenie wartosci: 0,0625*C na bin
#         pomiar = str2int * 1 # Do podmienienia przelicznik
#         SR04List.append(pomiar)
#         loopend = (time.time() - start)
#         print(loopend)
#         print(MUPsettings.Addr)
# 
#     # F1
#     elif MUPsettings.Addr == '06': # Belka tensometryczna NA27 | podaje wartośćśrednią W | brak WL WH | 
#         loopend = (time.time() - start)
#         print(loopend)
#         print(MUPsettings.Addr)
# 
#     # F2
#     elif MUPsettings.Addr == '07': # SparkFun HX711
#         loopend = (time.time() - start)
#         print(loopend)
#         print(MUPsettings.Addr)
# 
#     # RTC
#     elif MUPsettings.Addr == '05':
#         loopend = (time.time() - start)
#         print(loopend)
#         print(MUPsettings.Addr)
# 
#     # ADC1
#     elif MUPsettings.Addr == '03':
#         loopend = (time.time() - start)
#         print(loopend)
#         print(MUPsettings.Addr)

    # Zabezpieczenie przed bledami
    else:
#         print(str(MUPsettings.Addr) + " #")
        return

    return;


##################### Program glowny #####################
# Wlaczenie wielowatkowosci
stoper_thread = threading.Thread(target = stoper)
stoper_thread.start()

### PETLA GLOWNA
while True:
    start = time.time()
#     bytesToRead = SerialData.inWaiting()

    # Odbierz byte z buforu
    SR = SerialData.read()

    # Konwersja
    SR2hex = SR.hex()
    SR2int = int(SR2hex, 16)
#     SR2bin = format(SR2int, '08b')

    # Podglad otrzymywanych znakow: str|int|hex|bin
#     tab = "\t"
#     print(f"{str(SR) + tab + str(SR2int) + tab + str(SR2hex) + tab + str(SR2bin)}")

    # Funkcja rozpoznania ramki
    checkFrame(SR2int)
    
#     loopend = (time.time() - start)
#     print(loopend)


    #sleep(.5)
    #if SR2int == 10:
#     print(SR)

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
