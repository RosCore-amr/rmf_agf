#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import jwt
import uvicorn

import json
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from threading import Thread
from mongodb import MongoDB, AGF_System_DB_Collection
import requests

db = MongoDB("mongodb://localhost:27017/")

app = FastAPI(
    title="Robot API",
    openapi_url="/openapi.json",
    docs_url="/docs",
    description="controlsystem",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Mission(BaseModel):
    id: str
    type: int
    line: str


class Location(BaseModel):
    location_code: str
    robot_point: str
    detect_point: str


class ApiServer:

    @app.get("/predict")
    def get_res():
        # test =
        task = {}
        return {"test": task}

    @app.post("/occuppy_mission")
    def occuppy_mission(mission: Mission):

        _find_mission = db.MongoDB_findone(
            AGF_System_DB_Collection.MISIONS, {"mission_id": mission.id}
        )
        if _find_mission is not None:
            return {"code": "NG"}

        location = "CTT"
        if int(mission.type) == 1:
            location = "CTT"
        elif int(mission.type) == 2:
            location = "NHUA"

        _mission = {
            "mission_id": mission.id,
            "line": mission.line,
            "type": mission.type,
            "location": location,
            "mission_status": 7,
        }

        _occupy_mission = db.MongoDB_insert(AGF_System_DB_Collection.MISIONS, _mission)
        return {"code": "OK"}

    @app.post("/add_location")
    def add_location(location: dict):
        _location = db.MongoDB_findone(
            AGF_System_DB_Collection.LOCATIONS,
            {"location_code": location["location_code"]},
        )
        if _location is not None:
            return {"code": 0}
        _location_add = db.MongoDB_insert(AGF_System_DB_Collection.LOCATIONS, location)
        return {"code": 1}

    @app.get("/locations")
    def get_locations():
        _location_add = db.MongoDB_find(AGF_System_DB_Collection.LOCATIONS, {})
        return _location_add

    @app.post("/confirm_mission")
    def comfirm_mission(mission: dict):
        search_value = {"mission_id": mission["mission_id"]}

        update_mission_status = db.MongoDB_update(
            AGF_System_DB_Collection.MISIONS, search_value, mission
        )
        return update_mission_status

    @app.post("/progress_mission")
    def progress_mission(mission: dict):

        _mission_sent_andon = {
            "id": mission["mission_id"],
            "_status": mission["mission_status"],
        }
        sent_mission_to_andon(_mission_sent_andon)

        search_value = {"mission_id": mission["mission_id"]}
        _misison_update = {
            "mission_id": mission["mission_id"],
            "mission_status": mission["mission_status"],
        }
        update_robot_status = db.MongoDB_update(
            AGF_System_DB_Collection.MISIONS, search_value, _misison_update
        )
        return update_robot_status

    @app.post("/robot_status/AGF_1")
    def robot_status(robot: dict):

        search_value = {"robot_code": "AGF_1"}
        robot.update(search_value)
        update_robot_status = db.MongoDB_update(
            AGF_System_DB_Collection.STATUS_RB, search_value, robot
        )

        return {"code": 1}

    @app.post("/sent_mission_robot")
    def sent_mission_robot(mission: dict):
        _sent = sent_mission_to_robot(mission)

        # search_value = {"robot_code": "AGF_1"}
        # robot.update(search_value)
        # update_robot_status = db.MongoDB_update(
        #     AGF_System_DB_Collection.STATUS_RB, search_value, robot
        # )

        return _sent

    @app.post("/sent_mission_ando")
    def sent_mission_ando(mission: dict):
        _sent = sent_mission_to_andon(mission)
        return _sent


def status_poll():
    while True:
        # print("hello")
        _find_agf = db.MongoDB_findone(
            AGF_System_DB_Collection.STATUS_RB, {"robot_code": "AGF_1"}
        )
        # mission_run = mapping_mission()
        if _find_agf is not None:
            if (
                _find_agf["work_status"]["agf_status"] == 1
                and _find_agf["work_status"]["agf_work_mode"] == "Auto"
            ):
                mission_run = mapping_mission()
                if mission_run["code"]:
                    _sent = sent_mission_to_robot(mission_run)
                    print("_sent", _sent)
                    # pass
                # print("robotr here")
                # pass

        time.sleep(2)


def mapping_mission():
    _find_mission_wait = db.MongoDB_findone(
        AGF_System_DB_Collection.MISIONS, {"mission_status": 1}
    )
    if _find_mission_wait is None:
        return {"code": 0}

    position_second = str(_find_mission_wait["line"] + "_" + "01")

    _location_pick_second = db.MongoDB_findone(
        AGF_System_DB_Collection.LOCATIONS,
        {"location_code": position_second},
    )

    _location_pick = db.MongoDB_findone(
        AGF_System_DB_Collection.LOCATIONS,
        {"location_code": _find_mission_wait["location"]},
    )

    _location_put = db.MongoDB_findone(
        AGF_System_DB_Collection.LOCATIONS,
        {"location_code": _find_mission_wait["line"]},
    )

    # _location_finishs_gooods = db.MongoDB_findone(
    #     AGF_System_DB_Collection.LOCATIONS,
    #     {"location_code": _find_mission_wait["line"]},
    # )

    # _location_return_finish_location = db.MongoDB_findone(
    #     AGF_System_DB_Collection.LOCATIONS,
    #     {"location_code": "TRA"},
    # )

    if (
        _location_pick is None
        or _location_put is None
        or _location_pick_second is None
        # or _location_return_finish_location is None
    ):
        # print("errror")
        return {"code": 0}

    # position_second = str(_find_mission_wait["line"] + "_" + "01")
    # print("asdasd", position_second)

    task = {
        "mission_id": _find_mission_wait["mission_id"],
        "task_list": [
            # {"task_name": "navigation", "target_point": "LM44"},
            {
                "task_name": "pick",
                "pick_point": _location_pick["robot_point"],
                "detect_point": _location_pick["detect_point"],
            },
            {"task_name": "put", "put_point": _location_put["robot_point"]},
            {
                "task_name": "pick",
                "pick_point": _location_pick_second["robot_point"],
                "detect_point": _location_pick_second["detect_point"],
            },
            {
                "task_name": "put",
                "put_point": "LM15",
            },
            {"task_name": "navigation", "target_point": "LM137"},
            # {
            #     "task_name": "pick",
            #     "pick_point": _location_pick["robot_point"],
            #     "detect_point": _location_pick["robot_point"],
            # },
            # {"task_name": "put", "put_point": _location_put["robot_point"]},
        ],
        "agf_id": 1,
        "code": 1,
        "loop": False,
        "work_mode": "Auto",
    }
    return task


def sent_mission_to_andon(mission):
    _url_request = "http://10.122.79.60/api/AGF_Response/data"
    # _request_body = {
    #     "id": mission["mission_id"],
    #     "mission_status": mission["mission_status"],
    # }
    # print("herrrrr", _request_body)
    try:
        res = requests.post(
            _url_request,
            json=mission,
            timeout=4,
        )
        response = res.json()
        print("response", response)

        return response
    except Exception as e:
        # print(e)
        return {"code": 0}


def sent_mission_to_robot(mission):
    _url_request = "http://192.168.1.237:8000/task_chain"
    # _request_body = {
    #     "id": mission["mission_id"],
    #     "mission_status": mission["mission_status"],
    # }
    # print("herrrrr", _request_body)
    try:
        res = requests.post(
            _url_request,
            json=mission,
            timeout=4,
        )
        response = res.json()
        # print("response", response)

        return response
    except Exception as e:
        # print(e)
        return {"code": 0}


server = ApiServer()
if __name__ == "__main__":

    task1 = Thread(target=status_poll, args=())
    task1.start()

    print("Swagger run http://0.0.0.0:9000/docs#/")
    uvicorn.run(app, host="0.0.0.0", port=9000)
