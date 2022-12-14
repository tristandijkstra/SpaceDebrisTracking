import numpy as np
import pandas as pd
import requests
from datetime import datetime
import os
import io
# import datetime


def getSpactrackClient(folder="keys"):
    """Read keys file and return spacetrack client

    Args:
        folder (str, optional): folder name. Defaults to "keys".

    Raises:
        ValueError: if file does not exist return an error

    Returns:
        _type_: _description_
    """
    keyfile = f"{folder}/spacetrack.txt"
    if os.path.exists(keyfile):
        with open(keyfile, "r") as kf:
            username, password = kf.read().split("\n")
        return username, password

    else:
        raise ValueError("No key files given: add a file:'keys/spacetrack.txt'")

def formatDates():
    pass


def query(
    username:str,
    password:str,
    NORADid: int,
    start:datetime,
    end:datetime,
):
    startS = str(start)
    endS = str(end)

    print(startS)
    print(endS)

    logonURL = 'https://www.space-track.org/ajaxauth/login'
    gpURL = "https://www.space-track.org/basicspacedata/query/class/gp_history/"
    template = gpURL + f"NORAD_CAT_ID/{NORADid}/EPOCH/>2020-1-1,<2022-1-1/orderby/EPOCH asc/format/csv/"

    creds = {"identity":username, "password":password}
    with requests.Session() as sesh:
        cookie = sesh.post(logonURL, data=creds)

        res = sesh.get(template)
        if res.status_code != 200:
            print(res)
            raise ValueError(res, "GET fail on request")
        else:
            print(res.text)
        
        if len(res.text) > 2:                
            data = io.StringIO(res.text)
            P = pd.read_csv(data)
            print(P)
            P.to_csv("data/hi.csv")
        else:
            print(res.status_code)
            raise RuntimeError("File is empty, may be API overload")


if __name__ == "__main__":
    norads = [51092, 51062, 51081, 50987, 51032]
    start = datetime(2016,1,1)
    end = datetime(2023,1,1)
    username, password = getSpactrackClient()
    query(username, password, 51092, start, end)