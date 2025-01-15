from flask import Flask, jsonify, request
from flask_cors import CORS
from bson.objectid import ObjectId

from mongodb import MongoDB, AGF_System_DB_Collection

import time
from datetime import datetime

from logfile import LogFile


app = Flask(__name__)
CORS(app=app)


def read_mission_state(query=dict):
    try:
        return database.MongoDB_find(
            collection_name=AGF_System_DB_Collection.AGF_Mission_Pending, query=query
        )
    except Exception as e:
        return []


def add_mission_pending(mission: dict, mode: str) -> bool:
    current = datetime.now()
    date_recv = str(current.year) + "-" + str(current.month) + "-" + str(current.day)
    time_recv = (
        str(current.hour)
        + ":"
        + str(current.minute)
        + ":"
        + str(current.second)
        + ":"
        + str(current.microsecond)
    )
    mission["date_recv"] = date_recv
    mission["time_recv"] = time_recv
    mission["_id"] = mission["mission_id"]
    mission["agf_id"] = 0
    mission["work_mode"] = mode
    return database.MongoDB_insert(
        AGF_System_DB_Collection.AGF_Mission_Pending, mission
    )


@app.route("/mission/<mode>", methods=["POST"])
def post_mission(mode):
    try:
        if mode == "auto" or mode == "manual":
            content = request.json
            keys = content.keys()
            if (
                ("mission_id" in keys)
                and ("pallet_empty_warehouse" in keys)
                and ("pallet_full_warehouse" in keys)
                and ("pallet_empty_line" in keys)
                and ("pallet_full_line" in keys)
            ):
                if add_mission_pending(mission=content, mode=mode):
                    return jsonify({"result": True, "desc": ""}), 201
        return jsonify({"result": False, "desc": ""}), 204
    except Exception as e:
        return jsonify({"result": False, "desc": str(e)}), 500


if __name__ == "__main__":
    log = LogFile("./LogfileServer")
    log.init_logfile()
    database = MongoDB(
        "AGF_System_DB",
        [
            AGF_System_DB_Collection.AGF_Mission_Cancel,
            AGF_System_DB_Collection.AGF_Mission_Completed,
            AGF_System_DB_Collection.AGF_Mission_Executing,
            AGF_System_DB_Collection.AGF_Mission_Pending,
            AGF_System_DB_Collection.AGF_Mission_Undefined,
        ],
    )
    if not database.MongoDB_check():
        log.writeLog(type_log="error", msg="Database Init Error.")
        while True:
            time.sleep(1)
    log.writeLog(type_log="info", msg="Server Init Successed.")
    app.run(host="0.0.0.0", port=5001, debug=True)
