def checkFrame(B):
    global Addr, LenD, ComL, LF_flag, CR_flag, Addr_flag, LenD_flag, ComL_flag, Lenf, MSB, LSB, MData, checksum # Zmienne globalne zamiast lokalnych w def
    
    if B == 10: # Sprawdz czy znak '\n'
        LF_flag = 1
		Lenf += 1
    elif B == 13: # Sprawdz czy znak '\r'
        CR_flag = 1
		ComL_flag = 0
		Lenf += 1
    elif LF_flag == 1: # Sprawdz czy poprzedni znak byl koncem ramki -> Odczyt Addr
		if Lenf % 2 == 1:
			MSB = B
			Lenf += 1
		else:
			LSB = B
			Addr = (MSB << 8) | LSB
			Lenf += 1
			LF_flag = 0
			Addr_flag = 1
	elif Addr_flag == 1: # Sprawdz czy poprzedni znak byl adresem mastera -> Odczyt LenD
		if Lenf % 2 == 1:
			MSB = B
			Lenf += 1
		else:
			LSB = B
			LenD = (MSB << 8) | LSB
			Lenf += 1
			Addr_flag = 0
			LenD_flag = 1
    elif LenD_flag == 1: # Sprawdz czy poprzedni znak byl dlugoscia ramki -> Odczyt ComL
		if Lenf % 2 == 1:
			MSB = B
			Lenf += 1
		else:
			LSB = B
			ComL = (MSB << 8) | LSB
			Lenf += 1
			LenD_flag = 0
			ComL_flag = 1
	elif ComL_flag == 1: # Sprawdz czy poprzedni znak byl ComL -> Odczyt danych z mastera
		if Lenf % 2 == 1:
			MSB = B
			Lenf += 1
		else:
			LSB = B
			MData = (MSB << 8) | LSB
			Lenf += 1
	
	if LF_flag == 1: # Sprawdz czy ramka jest prawidlowa
		if Lenf == LenD: # <<< typy danych? <<
			checksum = 1
		else:
			checksum = 0
		
		
	
    return Lenf;
