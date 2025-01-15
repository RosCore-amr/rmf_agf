import pymongo
from pymongo import MongoClient
from bson import json_util, ObjectId
import json


class AGF_System_DB_Collection:

    AGF_MISSION = "missions"
    STATUS_RB = "status_robots"
    MISIONS = "missions"
    LOCATIONS = "locations"

    AGF_Mission_Pending = "AGF_Mission_Pending"
    AGF_Mission_Executing = "AGF_Mission_Executing"
    AGF_Mission_Completed = "AGF_Mission_Completed"
    AGFs_Info = "AGFs_Info"
    AGF_Mission_Cancel = "AGF_Mission_Cancel"
    AGF_Mission_Undefined = "AGF_Mission_Undefined"


class MongoDB:
    def __init__(self, connectionString="mongodb://localhost:27017"):
        self.client = MongoClient(connectionString)
        # self.collectionsDB = {}
        project = "zss"
        self.work_db = self.client[project]

    def MongoDB_insert(self, collection_name: str, data: dict) -> bool:
        try:
            collection = self.work_db[collection_name]
            _collection = collection.insert_one(data)
            return True
        except Exception as e:
            print(e)
            return False

    def MongoDB_detele(self, collection_name: str, data: dict) -> int:
        try:
            res = self.collectionsDB[collection_name].delete_one(data)
            return res.deleted_count
        except Exception as e:
            print(e)
            return -1

    def MongoDB_update(
        self, collection_name: str, search_value: dict, update: dict
    ) -> list:
        try:
            _collection = self.work_db[collection_name]
            # print("search_value", search_value)
            _update_value = {"$set": update}
            # _collection = collection.insert_one(query)
            _update = _collection.find_one_and_update(
                search_value,
                _update_value,
                # upsert=False,
            )
            # print("asdasd", _update)
            return True
        except Exception as e:
            # print(e)
            return False

    def MongoDB_find(self, collection_name: str, query: dict) -> list:
        try:
            _collection = self.work_db[collection_name]
            base = _collection.find(query)
            # print("sdasd", list(base))
            return self.json_payload(list(base))
        except Exception as e:
            print(e)
            return []

    def json_payload(self, value):
        return json.loads(json_util.dumps(value))

    def MongoDB_findone(self, collection_name: str, query: dict) -> list:
        try:
            _collection = self.work_db[collection_name]
            return _collection.find_one(query)
            # return list(self.collectionsDB[collection_name].find(query))
        except Exception as e:
            print(e)
            return None
