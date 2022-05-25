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
import numpy as np
from subprocess import call
import serial # https://pyserial.readthedocs.io/en/latest/pyserial_api.html
from time import sleep
# import time


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
    

# Zmienne globalne
Addr = 00
LenD = 00
ComL = 00
MSB = 0000
LSB = 0000
FByte = 00000000
bitCnt = 0
LenF = 0
CR_flag = 0
checksum = 0

def merge2byte(C):
    global MSB, LSB, FByte, bitCnt
    
    if bitCnt % 2 == 1:
        MSB = C
    else:
        LSB = C
        FByte = (MSB << 8) | LSB
    
    return;
    
    
# Odczyt danych z ramki
def readFrame(A):
    
    global Addr, LenD, ComL, MSB, LSB, FByte, bitCnt, LenF, CR_flag, checksum
        
    ## Znak /n
    if A == 10:
        
        # Sprawdz poprawnosc ramki (czy wystapil wczesniej znak CR)
        if CR_flag == 1:
            checksum = 1 # Ramka poprawna
            CR_flag = 0
        else:
            checksum = -1 # Ramka nieprawidlowa
        
        # Wyzeruj licznik ramki
        bitCnt = 1
        
    ## Znak /r
    elif A == 13:
        
        # Aktywuj flage, zwieksz licznik
        CR_flag = 1
        bitCnt += 1
    
    ## Pozostale elementy ramki
    else:
        
        # Sprawdz poprawnosc znakow (czy HEX)
        A -= 48 # znaki 0-9
        if A > 16:
            A -= 7 # znaki A-F
        if A > 16: # jesli nadal poza zakresem -> inne znaki (bledna ramka)
            checksum = -1
        else:
            
            # Znaki poprawne -> dalsza analiza ramki
            
            # Polacz znaki w byte
            merge2byte(A)
            bitCnt += 1
            
            # Adres
            if bitCnt == 2:
                Addr = FByte
                
            # Dlugosc ramki
            elif bitCnt == 4:
                LenD = FByte
                
            # ComL
            elif bitCnt == 6:
                ComL = FByte
                # Sprawdzenie poprawnosci ComL | ComL = 00h - LenD
                
            # Pozostale dane
            else:
                
                # Sprawdz dlugosc ramki
                if bitCnt >= LenD - 2:
                    checksum = -1
                    
                else:
                    
                    # Utworz tablice danych        
        
    
    return checksum;


# Analiza danych z ramki
def readFrameData(data):
    
    # Termometr A
    if Addr == 01h:
        
    # Termometr B
    elif Addr == 02h:
        
    # Termometr C
    elif Addr == 12h:
        
    # WDS
    elif Addr == 0Ch:
        
    # CPR
    elif Addr == 08h:
        
    # SHARP30
    elif Addr == 0Dh:
        
    # SR04
    elif Addr == 0Eh:
        
    # F1
    elif Addr == 06h:
        
    # F2
    elif Addr == 07h:
        
    # RTC
    elif Addr == 05h:
        
    # ADC1
    elif Addr == 03h:
        
    # Zabezpieczenie przed bledami
    else:
    
    
    return;


### PETLA GLOWNA
while True:
    #bytesToRead =SerialData.inWaiting()
    SR = SerialData.read()#.decode("ascii")
    SR2hex = SR.hex()
    SR2int = int(SR2hex, 16)
    SR2bin = format(SR2int, '08b')
    tab = "\t"
    print(f"{str(SR) + tab + str(SR2int) + tab + str(SR2hex) + tab + str(SR2bin)}")
    #sleep(.5)
    #if SR2int == 10:
    #    print(SR)
    
    #print(bytesToRead)
    #if bytesToRead > 0:
    #    print(SR)
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
