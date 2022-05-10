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
    


# Konwersja bajtu HEX na DEC
def HEX2DEC():
    
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
