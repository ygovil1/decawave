import time
from sys import argv, exit
import pickle
import signal

import math
import os

import requests

import messageboard


# Get navigation information
def main():

    # Open messageboard
    mb = messageboard.MessageBoard("nav")
    print(mb)
    cmd = "directions"


    def signal_handler(*args):
        print("keyboard interrupt")
        exit()
    # set up signal handler to stop while loop
    signal.signal(signal.SIGINT, signal_handler)

    # Define default values
    x_pix, y_pix = 250, 70
    move_direction = "x"
    move_magnitude = 0
    floor = 2

    while(True):
        # first, read x_pos, y_pos, angle, and floor from Yash's tags
        target = ["state", "updated_state"]
        msg_list = mb.readMsg(target)
        # print("1")
        if len(msg_list) > 0:
                msg = msg_list[-1] # get most recent one message
                x_pix = msg["x_pos_pixels"]     # FINAL
                y_pix = msg["y_pos_pixels"]     # FINAL
                floor = msg["floor"]            # FINAL

        # communicate with server
        url = "http://drjava.herokuapp.com/getinstruction"
        payload = {
            "xpos": x_pix,
            "ypos": y_pix,
            "floor": floor
        }
        # print("Getting Response")
        response = requests.get(url, params=payload)
        respDict = response.json()
        # print(respDict)

        mb.postMsg(cmd, respDict)

        time.sleep(0.1)



# -----------------------------------------------------------------------

if __name__ == "__main__":
    main()
