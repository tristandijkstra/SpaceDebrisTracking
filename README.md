# SpaceDebrisTracking
Space Debris Radar Tracking Capabilities assessment | Microsat Engineering project

## Usage
```py
from extract.extract import getTLEsFromLaunches, getCredentials
from datetime import datetime

start = datetime(2016, 1, 1)
end = datetime(2023, 1, 1)

token = getCredentials(source="discos")
username, password = getCredentials(source="spacetrack")

launchIDs = ["2013-066", "2018-092", "2019-084", "2022-002"]

# standard method, with combined TLEs
discosDataDict, launchesTLEDict = getTLEsFromLaunches(
    username,
    password,
    token,
    launchIDs,
    start,
    end,
    combineDiscosAndTLE=True,
    collectLaunches=False,
    forceRegen=False,
)

print(launchesTLEDict["2013-066"][39416])

# combining everything into one DF
discosDataDict, df = getTLEsFromLaunches(
    username,
    password,
    token,
    launchIDs,
    start,
    end,
    combineDiscosAndTLE=True,
    collectLaunches=True,
    collectAllTLEs=True,
    forceRegen=False,
)

print(df)
```