import numpy as np
import pandas as pd
from spacetrack import SpaceTrackClient
import spacetrack.operators as op
from datetime import datetime
import os
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
        with open(keyfile, 'r') as kf:
            username, password = kf.read().split("\n")
        client = SpaceTrackClient(username, password)
        return client

    else:
        raise ValueError("No key files given: add a file:'keys/spacetrack.txt'")
    

def query(NORADid:int, start, end,):
    st.tle_publish(format="tle", order+by)


if __name__ == "__main__":
    norads = [51092, 51062, 51081, 50987, 51032]
    drange = op.inclusive_range(datetime(2019, 6, 26), datetime(2019, 6, 27))
    norads = [51092, 51062, 51081, 50987, 51032]
    st = getSpactrackClient()
    lines = st.tle(iter_lines=True, publish_epoch=drange, orderby='TLE_LINE1', format='tle')
    # with open('tle.txt', 'w') as fp:
    #     for line in lines:
    #         fp.write(line)



