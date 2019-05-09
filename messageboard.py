import sys
import time
import pymongo
import datetime

from sys import argv, exit

class MessageBoard():
    MONGO_SERVER = "mongodb://admin:drjava@192.168.1.10:27017"
    MONGO_DATABASE = "robot"
    MONGO_COLLECTION = "master"

    def _toEpoch(self, time):
        return (time - datetime.datetime(1970,1,1)).total_seconds()

    def __init__(self, modulename, ip_addr=None):
        self.module = modulename
        # TODO: process ip_addr

        self.conn = self.client = pymongo.MongoClient(self.MONGO_SERVER)
        self.db   = self.conn.robot
        self.c = self.db[self.MONGO_COLLECTION]


        self.first = self.c.find().sort('$natural', pymongo.ASCENDING).limit(-1).next()
        self.tss = {}
        self.creation = self._toEpoch(datetime.datetime.utcnow())

    def __str__(self):
        s = ""
        s += "Mongo server: " + self.MONGO_SERVER + "\n"
        s += "Mongo database: " + self.MONGO_DATABASE + "\n"
        s += "Mongo collection: " + self.MONGO_COLLECTION + "\n"
        s += "Module: " + self.module
        return ("MessageBoard:\n" + s)

    def postMsg(self, cmd, message):
        message["ts"] = self._toEpoch(datetime.datetime.utcnow())
        message["module"] = self.module
        message["cmd"] = cmd
        self.c.insert_one(message)

    # toRead should specify the modules to read from,
    # and the cmds to read from each modules - list of lists 
    # IMPORTANT CHANGE: takes a list instead of list of lists
    # getAll is a Boolean, if True then returns all messages from all modules 
    # since messageboard creation
    # sinceCreation is a Boolean, if True returns all messages from target 
    # module since creation
    # Returns all messages posted by a target module-cmd since the last time 
    # readMsg was called for that module-cmd 
    def readMsg(self, toRead, getAll = False, ts = None, sinceCreation = False):        
        now = self._toEpoch(datetime.datetime.utcnow())
        # convert to tuple
        toRead = (toRead[0], toRead[1])

        info = []
        if ts == None:
            if toRead not in self.tss: 
                ts = self.creation
            else:
                ts = self.tss[toRead]

            if sinceCreation:
                ts = self.creation
        else:
            ts = now - ts
            print("Reading since: " + str(ts))

        #  iterate over each item to construct query
        query = {}
        module = toRead[0]
        cmd = toRead[1]

        query = {
            "ts": {"$gte": ts},
            "$and": [
                {"module": module},
                {"cmd": cmd}
            ]
        }

        if getAll:
            query = { "ts": {"$gte": self.creation} }

        # print(query)

        cursor = self.c.find(query,
                    cursor_type=pymongo.CursorType.TAILABLE_AWAIT)
        for doc in cursor:
            # print(doc)
            info.append(doc)

        if len(info) > 0 and ts == None:
            self.tss[toRead] = now

        return info

#------------------------------------------------------------------------------

def main():
    # Start message board, linked with module “test_module2”
    print("Starting MessageBoard...")
    mb = MessageBoard("test_module2")
    print(str(mb))

    # sample message to send - dict with the optional fields
    test_msg = {
        "x_pos": 10,
        "y_pos": 15,
    }

    # posting a message
    print("Posting...")
    mb.postMsg("test", test_msg)

    # specify the targets to read from
    # should be a list of lists
    # each internal list of format: [ “module”, “cmd” ]
    print("Reading...")
    targets = ["test_module2", "test"]

    if len(argv) > 2:
        targets = [argv[1], argv[2]]

    # specify a duration in seconds to look back
    begin_ts = 300

    # read messages from targets since last read
    # returns a list of dicts (each msg is a dict)
    msg = mb.readMsg(targets)
    for item in msg:
        print(item)


    # read messages from targets in the past 20 min (value of begin_ts)
    # returns a list of dicts (each msg is a dict)
    msg2 = mb.readMsg(targets, ts = begin_ts)
    for item in msg2:
        print(item)



#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()


#db.create_collection(
#  MONGO_COLLECTION,
#  size=100000,
#  max=100,
#  capped=True
#)

# Run this script with any parameter to add one record
# to the empty collection and see the code below
# loop correctly
#

#c.insert_one(
#    {
#      "cmd" : "emergencyStop",
#      "ts" : <now>
#    }
#  )


# Get a tailable cursor for our looping fun
# while True:
#     # For a regular capped collection CursorType.TAILABLE_AWAIT is the
#     # only option required to create a tailable cursor. When querying the
#     # oplog the oplog_replay option enables an optimization to quickly
#     # find the 'ts' value we're looking for. The oplog_replay option
#     # can only be used when querying the oplog.
#     cursor = c.find({'_id': {'$gt': ts}},
#                         cursor_type=pymongo.CursorType.TAILABLE_AWAIT)
#     while cursor.alive:
#         for doc in cursor:
#             ts = doc['_id']
#             print(doc)
#         # We end up here if the find() returned no documents or if the
#         # tailable cursor timed out (no new documents were added to the
#         # collection for more than 1 second).
#         time.sleep(1)
