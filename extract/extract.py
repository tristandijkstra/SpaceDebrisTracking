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
    keyfile = os.path.normpath(__file__ + "../../../keys/spacetrack.txt")
    if os.path.exists(keyfile):
        with open(keyfile, "r") as kf:
            username, password = kf.read().split("\n")
        return username, password

    else:
        raise ValueError("No key files given: add a file:'keys/spacetrack.txt'")


def formatDates():
    pass


def query(
    username: str,
    password: str,
    NORADid: int,
    start: datetime,
    end: datetime,
    saveFolder="data",
    forceRegen: bool = False
):
    if not os.path.exists(saveFolder):
        os.makedirs(saveFolder)

    startS = str(start)
    endS = str(end)

    logonURL = "https://www.space-track.org/ajaxauth/login"
    gpURL = "https://www.space-track.org/basicspacedata/query/class/gp_history/"
    template = (
        gpURL
        + f"NORAD_CAT_ID/{NORADid}/EPOCH/>2020-1-1,<2022-1-1/orderby/EPOCH asc/format/csv/"
    )

    saveFilePath = f"{saveFolder}/{NORADid}.csv"
    if not os.path.exists(saveFilePath) or forceRegen:
        creds = {"identity": username, "password": password}
        with requests.Session() as sesh:
            cookie = sesh.post(logonURL, data=creds)

            res = sesh.get(template)
            if res.status_code != 200:
                print(res)
                raise ValueError(res, "GET fail on request")
            else:
                pass

            if len(res.text) > 2:
                data = io.StringIO(res.text)
                P = pd.read_csv(data)
                # P.to_csv(saveFilePath)
            else:
                print(res.status_code)
                raise RuntimeError("File is empty, may be API overload")

            droplist = [
                "CCSDS_OMM_VERS",
                "COMMENT",
                "CREATION_DATE",
                "ORIGINATOR",
                "REF_FRAME",
                "TIME_SYSTEM",
                "MEAN_ELEMENT_THEORY",
                "EPHEMERIS_TYPE",
                "CLASSIFICATION_TYPE",
                "SITE",
                "FILE",
                "GP_ID",
            ]
            # print([u for u in P.columns if u not in droplist])

            # dform = "%d-%m-%Y %H:%M:%S"
            dform = "%Y-%m-%dT%H:%M:%S.%f"
            P = (
                P.drop(columns=droplist)
                .assign(EPOCH=lambda x: pd.to_datetime(x.EPOCH, format=dform))
                .assign(LAUNCH_DATE=lambda x: pd.to_datetime(x.LAUNCH_DATE, format=dform))
                .assign(TLE_LINE1min1=lambda x: x.shift(1).TLE_LINE1)
                .assign(TLE_LINE2min1=lambda x: x.shift(1).TLE_LINE2)
                .assign(deltat=lambda x: (x.EPOCH - x.shift(1).EPOCH).dt.total_seconds())
                .drop(index=0)

            )
            P.to_csv(saveFilePath)
            return P
    else:
        print(f"Data for {NORADid} already generated")
        P = pd.read_csv(saveFilePath, index_col=0)
        return P

def discos(
    launchID: str,
    saveFolder: str = "discos",
    forceRegen: bool = False 
):
    """_summary_

    Args:
        launchID (str): the launch ids 
        saveFolder (str, optional): location of the folder . Defaults to "discos".
        forceRegen (bool, optional): can change to true if you want to rewrite the folders . Defaults to False.

    Returns:
        _type_: _description_
    """
    if not os.path.exists(saveFolder):
            os.makedirs(saveFolder)
    saveFilePath = f"{saveFolder}/{launchID}.csv"

    if not os.path.exists(saveFilePath) or forceRegen:
        print(f"Generating for launch: {launchID}") 
        URL = 'https://discosweb.esoc.esa.int'
        token = 'IjE0OGI4MzhlLWQ3ZGEtNGNhMS1hMjY4LWEzOTM5ZTY4ZWZjMCI.zTYeKlbcwFL6gWcd-heKTs3Soto'

        response = requests.get(
            f'{URL}/api/objects',
            headers={
                'Authorization': f'Bearer {token}',
                'DiscosWeb-Api-Version': '2',
            },
            params={
                'filter': f"eq(launch.cosparLaunchNo,'{launchID}')",
                'sort': '-reentry.epoch',

            },
        )

        doc = response.json()

        b = [] #extracting data
        for u in doc["data"]:
            i =  u["attributes"]
            b.append(i)
        df = pd.DataFrame.from_dict(b) #makes a dictonary of data
        satnumber = df.satno.values.tolist() #extracts satno coloumn
        df.to_csv(saveFilePath) 

        return df, satnumber


    else:
        P = pd.read_csv(saveFilePath, index_col=0)
        satnumber = P.satno.values.tolist()# type: ignore
        return P, satnumber

def discosweb(launchIDs: list):
    datafram = {} #dataframe
    norad = {} #satno
    for x in launchIDs:
        P = discos(x)
        P, norads = discos(x)
        datafram[x] = P
        norad[x] = norads
    return datafram, norad


if __name__ == "__main__":
    norads = [51092, 51062, 51081, 50987, 51032]
    start = datetime(2016, 1, 1)
    end = datetime(2023, 1, 1)
    username, password = getSpactrackClient()
    q = query(username, password, 27386, start, end, forceRegen=False)
    id = ['2013-066', '2018-092', '2019-084', '2022-002']
    discosweb(id)

    print(q)
    # print(q.dtypes)
