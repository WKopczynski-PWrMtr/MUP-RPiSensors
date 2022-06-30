def tohex(val, nbits):
  return hex((val + (1 << nbits)) % (1 << nbits))
# hx=tohex(0-2, 8)

def checkFrame(A):
    global Addr, LenD, ComL, MSB, LSB, FByte, bitCnt, CR_flag, checksum, Data, SR2hex, startTime, timeRecv
#     timeRecv = time.time()

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
                
                
    return checksum;
