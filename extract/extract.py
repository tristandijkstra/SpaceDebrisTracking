import numpy as np
import pandas as pd
import requests
from datetime import datetime
import os
import io
from typing import Tuple, Union, Dict, List
from tqdm import tqdm

# TODO this should be fixed
try:
    from . import measure
except:
    import measure

def getCredentials(source: str, folder="keys") -> Union[Tuple[str, str], str]:
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
    if source == "spacetrack":
        keyfile = os.path.normpath(__file__ + f"../../../{folder}/spacetrack.txt")
        if os.path.exists(keyfile):
            with open(keyfile, "r") as kf:
                username, password = kf.read().split("\n")
            return username, password

        else:
            raise ValueError(
                f"No key files given: add a file:'{folder}/spacetrack.txt'"
            )

    if source == "discos":
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
        username (str): username for spacetrack, can be retrieved using the getCredentials function
        password (str): password for spacetrack, can be retrieved using the getCredentials function
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
                    f"File is empty (status {res.status_code}), may be API overload or deorbitted spacecraft."
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

            # Add errors
            # NOTE yes this is a nasty apply
            # NOTE this can be improved, it has been left, so because of time constraints
            P[["errorX", "errorY", "errorZ", "overallCovariance"]] = P.apply(
                lambda x: measure.generateErrors(
                    x.TLE_LINE1, x.TLE_LINE2, x.TLE_LINE1min1, x.TLE_LINE2min1
                ),
                axis=1,
                result_type="expand",
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
    description: Union[str, None] = None,
) -> dict:
    """Query spacetrack for the TLE data of MULTIPLE NORAD ids over a specific period of time.
    Generate and save the data if it has not been generated already, then return this data in a dataframe.
    Return the cached dataframe otherwise.

    Args:
        username (str): username for spacetrack, can be retrieved using the getCredentials function
        password (str): password for spacetrack, can be retrieved using the getCredentials function
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

    errorNORADS = []

    for NORADid in tqdm(NORADidList, desc=description):
        # Retrieve and store TLE Data
        try:
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

        except Exception as e:
            errorNORADS.append(NORADid)
            print(f"Error in querySpacetrack: {e}, proceeding")

    if len(errorNORADS) > 0:
        print(f"Total failed: {len(errorNORADS)} -> {errorNORADS}")

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
        token (str): personal token for taken from getCredentials()
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
    token: str,
    launchIDs: list,
    saveFolder="data/discosweb",
    forceRegen=False,
    verbose=False,
):
    """retreives a dic of list of launch items in a launch id for multiple ids and a list of norad ids

    Args:
        token (str): personal token from discosweb taken from getCredentials
        launchIDs (list): list of launch id

    Returns:
        dataFrameDict: a dict with a set of pandas dataframes with discosweb tables of each launch
        noradsListDict: a dictionary with lists of NORAD ids for each launch
    """
    dataFrameDict = {}
    noradsListDict = {}

    for launchID in tqdm(launchIDs, desc="DiscosWeb"):
        P, noradsList = queryDiscosWeb(
            token, launchID, saveFolder, forceRegen, verbose=False
        )
        dataFrameDict[launchID] = P
        noradsListDict[launchID] = noradsList

    return dataFrameDict, noradsListDict


def getTLEsFromLaunches(
    spaceTrackUsername: str,
    spaceTrackPassword: str,
    discosWebToken: str,
    launchIDs: List[str],
    start: datetime,
    end: datetime,
    combineDiscosAndTLE: bool,
    collectLaunches: bool = True,
    collectAllTLEs: bool = False,
    forceRegen: bool = False,
    verbose: bool = False,
    saveFolder="data",
):# TODO add docstring - Momo attempted
    """if you want to return one big TLE Data frame this simplification is used

    Args:
        spaceTrackUsername (str): spacetrack username in keys > spacetrack.txt
        spaceTrackPassword (str): spacetrack password in keys > spacetrack.txt
        discosWebToken (str): discosweb token taken from keys > discosweb.txt (generated in discosweb)
        launchIDs (List[str]): list of launch ids 
        start (datetime): start date of the query 
        end (datetime): end date of the query 
        combineDiscosAndTLE (bool): Adds all Discos data to each of the relevant TLE dataframes
        collectLaunches (bool, optional): this combines the two dictionaries python 3.9+. Defaults to True.
        collectAllTLEs (bool, optional): combine all TLE dataframes into one. Defaults to False.
        forceRegen (bool, optional): force a regen of the data, even if the data had previously been cached. Defaults to False.
        verbose (bool, optional): print out extra information on the process. Defaults to False.
        saveFolder (str, optional): location to save the csv. Defaults to "data".

    Returns:
        _type_: returns a combined dataframe containing tle and discsos infomation -> discosDataDict, launchesTLEDict or launchesTLEDataFrame
    """

    
    

    
    collectLaunches = True if (collectAllTLEs == True) else False

    discosDataDict, noradsDict = queryDiscosWebMultiple(
        discosWebToken,
        launchIDs,
        forceRegen=forceRegen,
        verbose=verbose,
        saveFolder=f"{saveFolder}/discosweb",
    )
    launchesTLEDict: Union[dict, Dict[str, dict]] = {}


    for launchID in launchIDs:
        if verbose:
            print(f"\nRetrieving launch: {launchID}\n")

        NORADidList = noradsDict[launchID]

        TLEdict = querySpacetrackMultiple(
            spaceTrackUsername,
            spaceTrackPassword,
            NORADidList,
            start,
            end,
            saveFolder=f"{saveFolder}/{launchID}",
            forceRegen=forceRegen,
            verbose=verbose,
            description=f"Launch: {launchID}",
        )

        if combineDiscosAndTLE:
            # Add all Discos data to each of the relevant TLE dataframes (use pd.merge?)
            # TOD

            NORADidList = noradsDict[launchID]
          
            for s in NORADidList:
                df_cd = pd.merge(discosDataDict[launchID], TLEdict[s], how='inner', left_on = 'cosparId', right_on = 'OBJECT_ID')
                df_cd.drop('OBJECT_ID',axis=1,inplace=True)
                return df_cd
            #pass


        if collectLaunches:
            # this combines the two dictionaries python 3.9+
            launchesTLEDict = launchesTLEDict | TLEdict
        else:
            launchesTLEDict[launchID] = TLEdict
            

    if collectAllTLEs:
        # combine all TLE dataframes into one (pd.concat?)
        # TODO
        launchesTLEDataFrame = None
        pass
        return discosDataDict, launchesTLEDataFrame
    else:
        return discosDataDict, launchesTLEDict
    


if __name__ == "__main__":
    start = datetime(2016, 1, 1)
    end = datetime(2023, 1, 1)

    token = getCredentials(source="discos")
    username, password = getCredentials(source="spacetrack")

    launchIDs = ["2013-066", "2018-092", "2019-084", "2022-002"]

    discosDataDict, launchesTLEDict = getTLEsFromLaunches(
        username,
        password,
        token,
        launchIDs,
        start,
        end,
        combineDiscosAndTLE=False,
        collectLaunches=False,
        forceRegen=True,
    )



