import time
from sys import argv, exit
import pickle
import signal

import math
import os

import messageboard

# global variables
pix_to_met = 0.2
dist_error = 20 # cm??? what unit is the tag measurements in?

def pixels_to_meters(x_pix, y_pix):
    # @Yash: your conversion function
    # TODO:
    return (x_pix * pix_to_met, y_pix * pix_to_met)

# Update state
def main():

    # Open messageboard
    mb = messageboard.MessageBoard("state")
    print(mb)
    cmd = "updated_state"




    def signal_handler(*args):
        print("keyboard interrupt")
        exit()
    # set up signal handler to stop while loop
    signal.signal(signal.SIGINT, signal_handler)




    x_meters, y_meters = 0, 0
    x_pix, y_pix = 250, 70
    orientation = 0             # 0 = x, 1 = y, 2 = -x, 3 = -y
    orientation_angle = 0       # angle
    status = "dead"             # delivering / arrived / waiting / idle / dead
    angle = 0.0                 # if < 0, then ignore
    move_direction = "x"
    move_magnitude = 0
    floor = 2

    while(True):
        # first, read x_pos, y_pos, angle, and floor from Yash's tags
        target = ["tag", "location_data"] 
        msg_list = mb.readMsg(target)
        if len(msg_list) > 0:
            msg = msg_list[-1] # get most recent one message
            x_pix = msg["x_pix_global"]     # FINAL
            y_pix = msg["y_pix_global"]     # FINAL
            orientation_angle = msg["global_angle"]
            floor = msg["floor"]            # FINAL

        meters = pixels_to_meters(x_pix, y_pix)
        x_meters = meters[0]            # FINAL
        y_meters = meters[1]            # FINAL

        if math.fabs(orientation_angle) >= 0 and math.fabs(orientation_angle) <= 45:
            orientation = 0
        elif math.fabs(orientation_angle) >= 135 and math.fabs(orientation_angle) <= 180:
            orientation = 2
        elif 45 < orientation_angle and orientation_angle < 135:
            orientation = 1
        else:   # -135 < orientation_angle < -45
            orientation = 3             # FINAL

        # second, read corrected angle from Khanh's "angle" module
        target = ["angle", "angle_correction"] 
        msg_list = mb.readMsg(target)
        if len(msg_list) > 0:
            msg = msg_list[-1] # get most recent one message
            angle = msg["angle"]            # FINAL
        # NOTE TO COLLINS: this angle is different from Yash's because it's more
        # "fine-grained" and accurate than Yash's, which is just used to infer
        # crude orientation. This angle will be = -1 if my sensors know they're
        # not in a good place to get a good angle measurement, and will be a
        # positive angle less than 90 degrees if I'm in a good place to measure.
        # Based on this, you can infer how to "correct" the angle.


        # third, read move direction and magnitude from Yash's "nav" module
        target =  ["nav", "directions"] 
        msg_list = mb.readMsg(target)
        if len(msg_list) > 0:
            msg = msg_list[-1] # get most recent one message
            move_direction = msg["move_direction"]      # FINAL
            move_magnitude = msg["move_magnitude"]      # FINAL

        # last, update "status" appropriately
        if status == "dead":
            status = "idle"
        elif status == "idle" and len(msg_list) > 0:
            status = "delivering"
        elif status == "delivering":
            if move_magnitude <= 2:        #  2 m? what unit is "nav" in?
                status = "arrived"  # FINAL
        elif status == "arrived":
            # check Khanh's "door" module to see if at door yet
            target =  ["door", "location_correction"] 
            msg_list = mb.readMsg(target)
            if len(msg_list) > 0:
                msg = msg_list[-1] # get last known status
                if msg["at_door"]:
                    status = "waiting"
            # NOTE: "arrived" means near the office door, but not entirely sure
            # if at door. From "door" module, "waiting" means stopped at front of door.
        elif status == "waiting":
            time.sleep(300)       # wait 5 min ????? TODO: how to do this exactly? cuz rn, it just pauses the program and doens't post to MB for 5min
            status = "idle"

        msg = {
            "x_pos_meters": x_meters,
            "y_pos_meters": y_meters,
            "x_pos_pixels": x_pix,
            "y_pos_pixels": y_pix,
            "orientation": orientation,
            "angle": angle,
            "status": status,
            "move_direction": move_direction,
            "move_magnitude": move_magnitude,
            "floor": floor
        }

        mb.postMsg(cmd, msg)

        time.sleep(0.1)



# -----------------------------------------------------------------------

if __name__ == "__main__":
    main()
