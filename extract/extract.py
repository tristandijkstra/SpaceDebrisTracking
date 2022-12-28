import numpy as np
import pandas as pd
import requests
from datetime import datetime
import os
import io
from typing import Tuple
from tqdm import tqdm

# import datetime


def getkeys(route: str, folder="keys"):
    """Read keys file. for "discos" will return a token. for "spacetrack" will return username, password

    Args:
        route (str): it can be "spacetrack" or "discosweb"
        folder (str, optional):folder name. Defaults to "keys".

    Raises:
        ValueError: if file does not exist return an error

    Returns:
        for 'spacetrack' returns: username, password (str, str)
        for 'discosweb' returns: token (str)
    """
    if route == "spacetrack":
        keyfile = os.path.normpath(__file__ + f"../../../{folder}/spacetrack.txt")
        if os.path.exists(keyfile):
            with open(keyfile, "r") as kf:
                username, password = kf.read().split("\n")
            return username, password

        else:
            raise ValueError(
                f"No key files given: add a file:'{folder}/spacetrack.txt'"
            )

    if route == "discos":
        keyfile = os.path.normpath(__file__ + f"../../../{folder}/discosweb.txt")
        if os.path.exists(keyfile):
            with open(keyfile, "r") as kf:
                token = kf.read()
            return token
        else:
            raise ValueError(f"No key files given: add a file:'{folder}/discosweb.txt'")
    else:
        raise ValueError("No key files given/Error")


def querySpacetrack(
    username: str,
    password: str,
    NORADid: int,
    start: datetime,
    end: datetime,
    saveFolder="data",
    forceRegen: bool = False,
    verbose: bool = True,
) -> pd.DataFrame:
    """Query spacetrack for the TLE data of one NORADID over a specific period of time.
    Generate and save the data if it has not been generated already, then return this data in a dataframe.
    Return the cached dataframe otherwise.

    Args:
        username (str): username for spacetrack, can be retrieved using the getKeys function
        password (str): password for spacetrack, can be retrieved using the getKeys function
        NORADid (int): Norad id of the object
        start (datetime): start date of the query
        end (datetime): end date of the query
        saveFolder (str, optional): location to save the csv. Defaults to "data".
        forceRegen (bool, optional): force a regen of the data, even if the data had previously been cached. Defaults to False.
        verbose (bool, optional): print out extra information on the process. Defaults to True.

    Raises:
        ValueError: GET request failed for spacetrack
        RuntimeError: API may be overloaded

    Returns:
        pd.Dataframe: dataframe with TLE information of the NORAD object
    """

    if not os.path.exists(saveFolder):
        os.makedirs(saveFolder)

    dateformat = "%Y-%m-%d"
    startS = start.strftime(dateformat)
    endS = end.strftime(dateformat)

    logonURL = "https://www.space-track.org/ajaxauth/login"
    gpURL = "https://www.space-track.org/basicspacedata/query/class/gp_history/"
    queryStr = (
        f"NORAD_CAT_ID/{NORADid}/EPOCH/>{startS},{endS}/orderby/EPOCH asc/format/csv/"
    )
    template = gpURL + queryStr

    saveFilePath = f"{saveFolder}/{NORADid}.csv"
    if not os.path.exists(saveFilePath) or forceRegen:
        creds = {"identity": username, "password": password}
        with requests.Session() as sesh:
            cookie = sesh.post(logonURL, data=creds)

            res = sesh.get(template)
            if res.status_code != 200:
                print(res)
                raise ValueError(res, "GET fail on request")

            if len(res.text) > 2:
                data = io.StringIO(res.text)
                P = pd.read_csv(data)
            else:
                raise RuntimeError(
                    f"File is empty, may be API overload. status={res.status_code}"
                )

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

            dform = "%Y-%m-%dT%H:%M:%S.%f"
            P = (
                P.drop(columns=droplist)
                .assign(EPOCH=lambda x: pd.to_datetime(x.EPOCH, format=dform))
                .drop_duplicates("EPOCH")
                .assign(
                    LAUNCH_DATE=lambda x: pd.to_datetime(x.LAUNCH_DATE, format=dform)
                )
                .assign(TLE_LINE1min1=lambda x: x.shift(1).TLE_LINE1)
                .assign(TLE_LINE2min1=lambda x: x.shift(1).TLE_LINE2)
                .assign(
                    deltat=lambda x: (x.EPOCH - x.shift(1).EPOCH).dt.total_seconds()
                )
                .drop(index=0)
            )

            P.to_csv(saveFilePath)

            return P
    else:
        if verbose:
            print(f"Data for {NORADid} already generated")

        dform = "%Y-%m-%dT%H:%M:%S.%f"
        P = (
            pd.read_csv(saveFilePath, index_col=0)
            .assign(EPOCH=lambda x: pd.to_datetime(x.EPOCH, format=dform))
            .assign(LAUNCH_DATE=lambda x: pd.to_datetime(x.LAUNCH_DATE, format=dform))
        )

        return P


def querySpacetrackMultiple(
    username: str,
    password: str,
    NORADidList: list,
    start: datetime,
    end: datetime,
    saveFolder="data",
    forceRegen: bool = False,
    verbose: bool = False,
) -> dict:
    """Query spacetrack for the TLE data of MULTIPLE NORAD ids over a specific period of time.
    Generate and save the data if it has not been generated already, then return this data in a dataframe.
    Return the cached dataframe otherwise.

    Args:
        username (str): username for spacetrack, can be retrieved using the getKeys function
        password (str): password for spacetrack, can be retrieved using the getKeys function
        NORADid (int): list of integer NORAD ids
        start (datetime): start date of the query
        end (datetime): end date of the query
        saveFolder (str, optional): location to save the csv. Defaults to "data".
        forceRegen (bool, optional): force a regen of the data, even if the data had previously been cached. Defaults to False.
        verbose (bool, optional): print out extra information on the process. Defaults to True.

    Raises:
        ValueError: GET request failed for spacetrack
        RuntimeError: API may be overloaded

    Returns:
        pd.Dataframe: dataframe with TLE information of the NORAD object
    """

    TLEdict = {}

    for NORADid in tqdm(NORADidList):
        # Retrieve and store TLE Data
        TLEdf = querySpacetrack(
            username,
            password,
            NORADid,
            start,
            end,
            saveFolder=saveFolder,
            forceRegen=forceRegen,
            verbose=verbose,
        )

        TLEdict[NORADid] = TLEdf

    return TLEdict
    

def queryDiscosWeb(
    token: str,
    launchID: str,
    saveFolder: str = "discos",
    forceRegen: bool = False,
    verbose: bool = True,
) -> Tuple[pd.DataFrame, list]:
    """retreives a dic of list of launch items in a launch id for one id and a list of norad id

    Args:
        token (str): personal token for taken from getkeys()
        launchID (str): the launch ids
        saveFolder (str, optional): location of the folder . Defaults to "discos".
        forceRegen (bool, optional): can change to true if you want to rewrite the folders . Defaults to False.

    Returns:
        pd.DataFrame: result from discosweb
        list: list of NORAD ids for given launch
    """
    if not os.path.exists(saveFolder):
        os.makedirs(saveFolder)
    saveFilePath = f"{saveFolder}/{launchID}.csv"

    if not os.path.exists(saveFilePath) or forceRegen:
        if verbose:
            print(f"Generating for launch: {launchID}")
        URL = "https://discosweb.esoc.esa.int"
        token = f"{token}"

        response = requests.get(
            f"{URL}/api/objects",
            headers={
                "Authorization": f"Bearer {token}",
                "DiscosWeb-Api-Version": "2",
            },
            params={
                "filter": f"eq(launch.cosparLaunchNo,'{launchID}')",
                "sort": "satno",
            },
        )

        doc = response.json()

        b = []  # extracting data
        for u in doc["data"]:
            b.append(u["attributes"])

        # makes a dictonary of data
        P = pd.DataFrame.from_dict(b)  # type: ignore
        # extracts satno coloumn
        satnumber = list(P.satno.values)

        P.to_csv(saveFilePath)

        return P, satnumber

    else:
        if verbose:
            print(f"DiscosWeb for launch: {launchID} already retrieved")

        P = pd.read_csv(saveFilePath, index_col=0)
        satnumber = list(P.satno.values)  # type: ignore
        return P, satnumber


def queryDiscosWebMultiple(
    token: str, launchIDs: list, saveFolder="data/discosweb", forceRegen=False
):
    """retreives a dic of list of launch items in a launch id for multiple ids and a list of norad ids

    Args:
        token (str): personal token from discosweb taken from getkeys
        launchIDs (list): list of launch id

    Returns:
        dataFrameDict: a dict with a set of pandas dataframes with discosweb tables of each launch
        noradsListDict: a dictionary with lists of NORAD ids for each launch
    """
    dataFrameDict = {}
    noradsListDict = {}

    for launchID in tqdm(launchIDs):
        P, noradsList = queryDiscosWeb(
            token, launchID, saveFolder, forceRegen, verbose=False
        )
        dataFrameDict[launchID] = P
        noradsListDict[launchID] = noradsList

    return dataFrameDict, noradsListDict


# def getData(launches:list, start:datetime, end:datetime):
#     # TODO FINISH
#     discosInfoDict, noradDict = discosweb(launches)

#     for launch in launches:
#         norads = noradDict[launch]
#         querySpacetrackList(norads)

#     pass


if __name__ == "__main__":
    NORADidList = [51092, 51062, 51081, 50987, 51032]
    start = datetime(2016, 1, 1)
    end = datetime(2023, 1, 1)

    token = getkeys(route="discos")
    username, password = getkeys(route="spacetrack")

    launchIDs = ["2013-066", "2018-092", "2019-084", "2022-002"]

    discosDataDict, noradsDict = queryDiscosWebMultiple(token, launchIDs, forceRegen=False)

    testDict = querySpacetrackMultiple(username, password, NORADidList, start, end)