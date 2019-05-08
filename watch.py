import sys
import time
import pymongo

MONGO_SERVER = "mongodb://admin:drjava@192.168.1.10:27017"
MONGO_DATABASE = "robot"
MONGO_COLLECTION = "master"

conn = client = pymongo.MongoClient(MONGO_SERVER)
db   = conn.robot

#db.create_collection(
#  MONGO_COLLECTION,
#  size=100000,
#  max=100,
#  capped=True
#)
c = db[MONGO_COLLECTION]

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

first = c.find().sort('$natural', pymongo.ASCENDING).limit(-1).next()
ts = first["_id"]

# Get a tailable cursor for our looping fun
while True:
    # For a regular capped collection CursorType.TAILABLE_AWAIT is the
    # only option required to create a tailable cursor. When querying the
    # oplog the oplog_replay option enables an optimization to quickly
    # find the 'ts' value we're looking for. The oplog_replay option
    # can only be used when querying the oplog.
    cursor = c.find({'_id': {'$gt': ts}},
                        cursor_type=pymongo.CursorType.TAILABLE_AWAIT)
    while cursor.alive:
        for doc in cursor:
            ts = doc['_id']
            print(doc)
        # We end up here if the find() returned no documents or if the
        # tailable cursor timed out (no new documents were added to the
        # collection for more than 1 second).
        time.sleep(1)




        
