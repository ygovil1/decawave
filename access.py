try:
    from serial import Serial
except:
    print("except")
    from pyserial import Serial
import time

PORT = '/dev/ttyACM0'
BAUDRATE = 115200

CLEAR = [0x0d, 0x0d]
ENTER = [0x0d]
BIGNUM = 10000
LES = b'les'
TIMEOUT = 0.5


# -----------------------------------------------------------------------

def clearSer(ser):
    ser.write(CLEAR)
    ser.read(BIGNUM)


# -----------------------------------------------------------------------

def byteToStr(bytes):
    return bytes.decode("utf-8")

# -----------------------------------------------------------------------

# get distance from anchors
def getDist(ser):
    clearSer(ser)

    # write les and send enter command to stop tag
    ser.write(LES)
    ser.write(ENTER)
    time.sleep(1)
    ser.write(ENTER)

    # clear starting nonsense
    ser.readline()
    ser.read(5)

    # read a few lines 
    lines = []
    for i in range(10):
        lines.append(ser.readline())

    print('dist')

    # get data
    distances = {}
    for line in lines:
        # split line into its parts
        parts = line.split(b' ')
        if len(parts) <= 1:
            print('skipped, len <= 1, len: ' + str(len(parts)))
            print(parts)
            continue

        # process each part
        for part in parts:
            # skip parts that are too short
            if len(part) < 20:
                print('skipped, len part: ' + str(len(part)))
                print(part)
                continue

            deviceBytes = part.split(b'[')[0]
            device = byteToStr(deviceBytes)
            # print(device)
            distanceBytes = part.split(b'=')[1]
            # print(distanceBytes)
            distance = float(byteToStr(distanceBytes))

            print(device + ": " + str(distance))

            if device in distances:
                info = distances[device]
                dist = info['dist']
                num = info['numMeasure']
                newSum = dist * num + distance
                num = num + 1
                newAve = newSum / num 
                info['dist'] = newAve
                info['numMeasure'] = num 
                distances[device] = info
            else:
                info = {}
                info['dist'] = distance
                info['numMeasure'] = 1
                distances[device] = info

    clearSer(ser)
    return distances

# -----------------------------------------------------------------------

def main():

    ser = Serial(port = PORT, baudrate = BAUDRATE, timeout = TIMEOUT)
    if not ser.is_open:
        ser.open()
    print(ser)

    clearSer(ser)

    distances = getDist(ser)
    print(distances)

    ser.close()


# -----------------------------------------------------------------------

if __name__ == "__main__":
    main()
