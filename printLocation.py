try:
    from serial import Serial
except:
    print("except")
    from pyserial import Serial

import time
from sys import argv, exit
import pickle
import signal

import math
import os

import messageboard

PORT1 = '/dev/ttyACM0'
PORT2 = '/dev/ttyACM1'
BAUDRATE = 115200

CLEAR = [0x0d, 0x0d]
ENTER = [0x0d]
BIGNUM = 10000
LES = b'les'
TIMEOUT = 0.5

PIX_TO_M_X = 0.2
PIX_TO_M_Y = 0.2

NAME_TO_POINT = {'1934': 50, '872D': 54, 'CB35': 53}

sorted_data = []
points_list = []

# Get point and static measurement data
with open('point_data_sorted_snd.pickle', 'rb') as infile1:
    sorted_data = pickle.load(infile1)

with open('points_list.pickle', 'rb') as infile2:
    points_list = pickle.load(infile2)

for i in range(len(points_list)):
    point = points_list[i]
    new_point = (int(point[0]), int(point[1]))
    points_list[i] = new_point

print(sorted_data)
print(points_list)

# -----------------------------------------------------------------------

def clearSer(ser):
    ser.write(CLEAR)
    ser.read(BIGNUM)

# -----------------------------------------------------------------------

def byteToStr(bytes):
    return bytes.decode("utf-8")

# -----------------------------------------------------------------------

# Reads one line from the decawave tag
def readLine(ser):
    line = ser.readline()
    # split line into its parts
    parts = line.split(b' ')
    if len(parts) <= 1:
        # print('skipped, len <= 1, len: ' + str(len(parts)))
        # print(line)
        return {}

    print(line)
    # process each part
    distances = {}
    for part in parts:
        # skip parts that are too short
        if len(part) < 20:
            # print('skipped, len part: ' + str(len(part)))
            # print(part)
            continue

        deviceBytes = part.split(b'[')[0]
        device = byteToStr(deviceBytes)
        # print(device)
        try:
            distanceBytes = part.split(b'=')[1]
            distance = float(byteToStr(distanceBytes))
        except:
            print("skip: " + str(part))
            continue
        # print(distanceBytes)
        distances[device] = distance

    return distances

# -----------------------------------------------------------------------

# Location conversion functions

RADIUS = 60

def distPixels(pixel1, pixel2):
    x1, y1 = pixel1
    x2, y2 = pixel2
    return math.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))

def findBotTop(dist, anchor_num, sorted_data):
    ret_data = {}
    dist_list = sorted(list(sorted_data[anchor_num].keys()))
    
    # find bottom and top index
    bot_ind = 0
    top_ind = 1
    for i in range(len(dist_list) - 1):
        botdist = dist_list[i]
        topdist = dist_list[i+1]
        bot_ind = i
        top_ind = i + 1
        if botdist < dist and topdist >= dist:
            break
    
    # Find best sandwiching points
    lo = bot_ind
    hi = top_ind
    found = False
    
    while lo >= 0:
        hi = top_ind
        
        botdist = dist_list[lo]
        topdist = dist_list[hi]
        botpoint = sorted_data[anchor_num][botdist][0][0]
        toppoint = sorted_data[anchor_num][topdist][0][0]
        # print("lo: " + str(lo) + ", consider: " + str(botpoint) + ", " + str(toppoint))
        botpixel = points_list[botpoint]
        toppixel = points_list[toppoint]
        separation = distPixels(botpixel, toppixel)
        if separation < RADIUS:
            found = True
            break
        
        while hi < len(dist_list):
            botdist = dist_list[lo]
            topdist = dist_list[hi]
            botpoint = sorted_data[anchor_num][botdist][0][0]
            toppoint = sorted_data[anchor_num][topdist][0][0]
#             print("hi: " + str(hi) + ", consider: " + str(botpoint) + ", " + str(toppoint))
            botpixel = points_list[botpoint]
            toppixel = points_list[toppoint]
            separation = distPixels(botpixel, toppixel)
            if separation < RADIUS:
                found = True
                break

            hi += 1
        
        if found:
            break
        
        lo -= 1

    if not found:
        lo = bot_ind
        hi = top_ind
    
    botdist = dist_list[lo]
    topdist = dist_list[hi]
    botpoint = sorted_data[anchor_num][botdist][0][0]
    toppoint = sorted_data[anchor_num][topdist][0][0]
    
    ret_data['botdist'] = botdist
    ret_data['topdist'] = topdist
    ret_data['botpoint'] = botpoint
    ret_data['toppoint'] = toppoint
    # print("ret_data for anch: " + str(anchor_num))
    # print(ret_data)
    return ret_data

# Linearly interpolate this distance using one anchor info
def linear_interp(dist, anchor_num, sorted_data):
    sorted_data_list = list(sorted_data[anchor_num].keys())
    
    bot_top_data = findBotTop(dist, anchor_num, sorted_data)
    
    topdist = bot_top_data['topdist']
    botdist = bot_top_data['botdist']
    botpixel = points_list[bot_top_data['botpoint'] -1]
    toppixel = points_list[bot_top_data['toppoint'] -1]
    x1, y1 = botpixel
    x2, y2 = toppixel
    
    dist_top_bot = topdist - botdist
    dist_this_bot = dist - botdist
    dist_this_top = topdist - dist
    
    mid1x = x1 * (dist_this_top / dist_top_bot) + x2 * (dist_this_bot / dist_top_bot)
    
    midx = mid1x
    midy = y1 * (dist_this_top/ dist_top_bot) + y2 * (dist_this_bot/ dist_top_bot)
    
    data = {}
    data['toppixel'] = toppixel
    data['botpixel'] = botpixel
    data['thispixel'] = (midx, midy)
    data['thisdist'] = dist
    data['topdist'] = topdist
    data['botdist'] = botdist
    return data


# Get location functions 
weights = {'CB35': 20, '1934': 0, '872D': 1, '0288': 10, '1485': 20}
middle_range = 3
elevator_range = 3
dist_scale_range = 15

def weighted_pixel_ave(weights, anch_predictions):
    sum = (0,0)
    weights_sum = 0
    for anch_loc, pred in anch_predictions.items():
        weight = weights[anch_loc]
        sum = (sum[0] + weight * pred[0], sum[1] + weight * pred[1])
        weights_sum += weight
        
    return (sum[0] / weights_sum, sum[1] / weights_sum)

# get location of tag given distances to anchors
def get_location(anch_dists):
#     print(weights)
    anch_predictions = {}
    for anch_loc, dist in anch_dists.items():
        this_prediction = linear_interp(dist, anch_loc, sorted_data)
        anch_predictions[anch_loc] = this_prediction['thispixel']
    
    copy_weights = dict(weights)
    tea_room = 'CB35'
    middle = '1934'
    middle_2 = '872D'
    elevator = '0288'
    
    # reign in middle error
    if tea_room in anch_predictions and middle in anch_predictions:
        dist_btw = distPixels(anch_predictions[tea_room], anch_predictions[middle])
        if dist_btw > 0:
            weight_scale = middle_range / dist_btw
    #         print("middle: " + str(dist_btw))
            copy_weights[middle] = copy_weights[middle] * weight_scale
    
    # reign in elevator error
    if tea_room in anch_predictions and elevator in anch_predictions:
        dist_btw = distPixels(anch_predictions[tea_room], anch_predictions[elevator])
        if dist_btw > 0:
            weight_scale = elevator_range / dist_btw
    #         print("elevator: " + str(dist_btw))
            copy_weights[elevator] = copy_weights[elevator] * weight_scale
        
    # scale weight by dist
    for anch_loc, dist in anch_dists.items():
        copy_weights[anch_loc] *= dist_scale_range / dist
        
    # weighted ave
#     print(copy_weights)
    ave = weighted_pixel_ave(copy_weights, anch_predictions)
        
    if ave[0] < 230:
        return anch_predictions, (ave[0]-1, ave[1])
    elif ave[0] < 310:
        return anch_predictions, (ave[0]+1, ave[1])

    return anch_predictions, (ave[0], ave[1])

# Get orientation of robot based on two tag locations
def get_angle(x1, y1, x2, y2):
    return math.atan2(x2-x1, y2-y1)


# -----------------------------------------------------------------------

# Read distances from Serial and add to a dict
def main():

    port1 = PORT1
    port2 = PORT2
    if len(argv) > 1:
        port1 = argv[1]

    if len(argv) > 2:
        port2 = argv[2]

    # Open serial connections
    ser1 = Serial(port = port1, baudrate = BAUDRATE, timeout = TIMEOUT)
    if not ser1.is_open:
        ser1.open()
    print(ser1)

    ser2 = Serial(port = port2, baudrate = BAUDRATE, timeout = TIMEOUT)
    if not ser2.is_open:
        ser2.open()
    print(ser2)

    # Open messageboard
    # mb = messageboard.MessageBoard("tag")
    # print(mb)
    cmd = "location_data"
    floor = 2
    status = "testing"

    name_to_point = NAME_TO_POINT


    def signal_handler(*args):
        print("keyboard interrupt")
        ser1.close()
        ser2.close()

        exit()

    # set up signal handler to stop while loop
    signal.signal(signal.SIGINT, signal_handler)

    clearSer(ser1)
    clearSer(ser2)

    # write les and send enter command to stop tag
    # ser.write(CLEAR)
    ser1.write(LES)
    ser1.write(ENTER)
    ser2.write(LES)
    ser2.write(ENTER)

    # clear starting nonsense
    ser1.readline()
    ser1.read(5)
    ser2.readline()
    ser2.read(5)    

    while(True):
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        lines = {}
        line1 = readLine(ser1)
        if len(line1) < 1:
            # print("no line - 1")
            pass
        else: 
            print("ACM0")
            lines[1] = line1
            line = line1

        line2 = readLine(ser2)
        if len(line2) < 1:
            # print("no line - 2")
            pass
        else: 
            print("ACM1")
            lines[2] = line2
            line = line2

        if len(lines) != 0:
            print(lines)

        if len(lines) == 0:
            continue
        elif len(lines) == 1:
            print('only 1 line')

            # get x, y coords
            dists = line 
            anch_pred, prediction = get_location(dists)
            x, y = prediction

            print(prediction)

        else:
            # get x, y coords
            dists1 = line1 
            anch_pred1, prediction1 = get_location(dists1)
            x1, y1 = prediction1

            dists2 = line2
            anch_pred2, prediction2 = get_location(dists2)
            x2, y2 = prediction2

            # get ave position
            x = (x1 + x2) / 2 
            y = (y1 + y2) / 2
            x_m = PIX_TO_M_X * x
            y_m = PIX_TO_M_Y * y

            # Check within bounds
            # if x > 87 and y > 87:
            #     continue

            # get angle
            angle = get_angle(x1, y1, x2, y2)
            print((prediction1, prediction2, angle))

        # msg = {
        #     "x_pix_global": x, 
        #     "y_pix_global": y,
        #     "x_meter_global": x_m, 
        #     "y_meter_global": y_m, 
        #     "floor": floor, 
        #     "status": status, 
        #     "angle": angle
        # }   

        # mb.postMsg(cmd, msg)


    ser.close()


# -----------------------------------------------------------------------

if __name__ == "__main__":
    main()
