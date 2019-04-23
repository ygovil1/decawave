try:
    from serial import Serial
except:
    print("except")
    from pyserial import Serial

import time
from sys import argv
import pickle

PORT = '/dev/ttyACM0'
BAUDRATE = 115200

CLEAR = [0x0d, 0x0d]
ENTER = [0x0d]
BIGNUM = 10000
LES = b'les'
TIMEOUT = 0.5



# -----------------------------------------------------------------------

def main():

    port = PORT
    if len(argv) > 1:
        port = argv[1]

    ser = Serial(port = port, baudrate = BAUDRATE, timeout = TIMEOUT)
    if not ser.is_open:
        ser.open()
    print(ser)

    clearSer(ser)

    distances = getDist(ser)
    print(distances)

    if len(argv) > 2 and len(distances) > 0:
        filenum = argv[2]
        filename = "static_measure_" + filenum + ".pickle"
        with open(filename, 'wb') as f:
            pickle.dump(distances, f)
            print("printed to: " + filename)

    ser.close()


# -----------------------------------------------------------------------

if __name__ == "__main__":
    main()
