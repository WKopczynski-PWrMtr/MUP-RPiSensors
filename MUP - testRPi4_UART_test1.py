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
FByte = 00000000  # msb + lsb
bitCnt = 0    # Licznik dlugosci ramki
CR_flag = 0   # Flaga znaku '\r'
checksum = 0  # Poprawnosc odebranej ramki
Addr3 = "12"


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


### Odczyt ramki ###
def checkFrame(A):
    global Addr, LenD, ComL,MSB, LSB, FByte, bitCnt, CR_flag, checksum
    
    ## Znak /n
    if A == 10:
        
        # Sprawdz poprawnosc ramki (czy wystapil wczesniej znak CR)
        if CR_flag == 1:
            checksum = 1 # Ramka poprawna
            CR_flag = 0  # Wyzerowanie flagi
        else:
            checksum = -1 # Ramka nieprawidlowa
            
        # Wyzeruj licznik ramki
        bitCnt = 1
        
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
            merge2byte(A)
            bitCnt += 1
#             print(FByte)
            
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
#                 tabb = "\t"
#                 print("Addr: " + str(Addr) + tabb + "LenD: " + str(LenD) + tabb + "ComL: " + str(ComL))
                
            # Pozostale dame
            else:
                # Utworz tablice danych
                return
            
#     print(bitCnt)
    return checksum;


### Analiza danych z ramki ###
def readFrameData(data):
    global Addr3, bitCnt
    
#     Addr2 = format(hex(int(Addr3, 16)), "02X")
    Addr2 = hex(int(Addr3, 16))
    
    # Termometr A
    if Addr2 == 0x01:
        print(Addr2)
        
    # Termometr B
    elif Addr2 == 0x02:
        print(Addr2)
        
    # Termometr C
    elif Addr2 == 0x12:
        print(Addr2)
        
    # WDS
    elif Addr2 == 0x0C:
        print(Addr2)
        
    # CPR
    elif Addr2 == 0x08:
        print(Addr2)
        
    # SHARP30
    elif Addr2 == 0x0D:
        print(Addr2)
        
    # SR04
    elif Addr2 == 0x0E:
        print(Addr2)
        
    # F1
    elif Addr2 == 0x06:
        print(Addr2)
        
    # F2
    elif Addr2 == 0x07:
        print(Addr2)
        
    # RTC
    elif Addr2 == 0x05:
        print(Addr2)
        
    # ADC1
    elif Addr2 == 0x03:
        print(Addr2)
        
    # Zabezpieczenie przed bledami
    else:
#         print(str(Addr2) + " #")
        return
    
    return;


### PETLA GLOWNA
while True:
#     start = time.time()
#     bytesToRead = SerialData.inWaiting()
    SR = SerialData.read()
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
    readFrameData(Addr)
#     loopend = (time.time() - start)
#     print(loopend)
#     print(Addr)
    
    
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
