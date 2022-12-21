import os
import sys
from typing import Tuple

import requests
import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from sgp4.api import Satrec, SGP4_ERRORS, days2mdhms, jday


# pandas assign(columnname: lambda x(do some stuff here using x))



MUearth = 398600  # km^..
Rearth = 6378.136  # km


def returnTestTLE():
    return "1 27386U 02009A   20001.54192287  .00000005  00000-0  15038-4 0  9994", "2 27386  98.1404  17.3951 0001257  86.5901  84.8559 14.37967408934480", "1 27386U 02009A   20001.82053934  .00000003  00000-0  14345-4 0  9998", "2 27386  98.1404  17.6591 0001254  86.7982  86.1169 14.37967399934527"

# def TLEoneLine(file):
#     TLE1_1 = file(:,29)
#     TLE1_2 = file(:,30)
#     TLE2_1 = file(:,27)
#     TLE2_2 = file(:,28)
#     dt = file(:,31)

#     return TLE1_1, TLE1_2, TLE2_1, TLE2_2, dt
    
    # Extract TLE1_1 = column 30, TLE1_2 = column 31, TLE2_1 = column 28, TLE2_2 = column 29


# Combine two definitions below, same inputs
# Extract csv columns in separate function (later)


def generateError(TLE1_1, TLE1_2, TLE2_1, TLE2_2, dt):
    satellite1 = Satrec.twoline2rv(TLE1_1, TLE1_2)
    satellite2 = Satrec.twoline2rv(TLE2_1, TLE2_2)

    mo1, d1, h1, m1, s1 = days2mdhms(satellite1.epochyr, satellite1.epochdays)
    mo2, d2, h2, m2, s2 = days2mdhms(satellite2.epochyr, satellite2.epochdays)

    jd2, fr2 = jday(satellite2.epochyr, mo2, d2, h2, m2, s2)

    e1, r1, v1 = satellite1.sgp4(jd2,fr2)
    e2, r2, v2 = satellite2.sgp4(jd2,fr2)

    r1 = np.asarray(r1) #in km
    r2 = np.asarray(r2) #in km

    error = r2 - r1 # True value minus calculated value

    return error

def AssignDF(error, file):
    file.assign(error_TLE = lambda x: generateError(x.TLE_LINE1MIN1, x.TLE_LINE2MIN1, x.TLE_LINE1, x.TLE_LINE2, x.dt))
    return file

# def AssignTest(error,file):
#     file.assign


    
    # JD, time, r, v, start, end, startTime, endTime = propagateSat(satellite1, 3, dt=1)
    # JD, time, r, v, start, end, startTime, endTime = propagateSat(satellite2, 3, dt=1)
    # # print(propagateSat(satellite1, 3, dt=1))
    # # print(propagateSat(satellite2, 3, dt=1))
    #a = returnLocation(satellite1, dt)
    #b = returnLocation(satellite2, 0)

    #error = a-b

# def returnLocation(satellite: Satrec, dt):
#     yr = satellite.epochyr
#     mo, d, h, m, s = days2mdhms(yr, satellite.epochdays)
#     epochStart = datetime(2000 + yr, mo, d, h, m, int(s)).timestamp()
#     epochStart += dt

#     startTime = datetime.fromtimestamp(epochStart)



#     trange = pd.date_range(startTime, startTime)
#     # get julian dates
#     t = trange.to_julian_date().to_numpy()
#     # split it between decimals and the integer
#     jd = np.floor(t).astype(np.int64)
#     fr = t - jd


#     e, r, v = satellite.sgp4(jd, fr)

    # return r








def propagateSat(satellite: Satrec, orbPeriods: int = 3, dt: float = 1, start=None, end=None) \
        -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float, datetime, datetime]:
    """Propagates satelite using SGP4, takes the current time and propagates over given orbital periods

    Args:
        satellite (Satrec): Satrec Satelite object
        orbPeriods (int, optional): integer amount of orbital periods. Defaults to 3.
        dt (float, optional): timestep in seconds. Defaults to 1.
        start (datetime, optional): timestep. Defaults to None.
        end (datetime, optional): timestep. Defaults to None.

        enter either orbital periods or a start and end time
    Returns:
        Tuple[np.ndarray np.ndarray, np.ndarray, datetime, datetime]: times, in km: position array, velocity array, start time, end time
    """

    orbPeriod = int(math.ceil(2 * math.pi * math.sqrt((satellite.a * Rearth) ** 3 / MUearth)))
    # print(f"OrbPeriod = {orbPeriod * orbPeriods}")

    yr = satellite.epochyr
    mo, d, h, m, s = days2mdhms(yr, satellite.epochdays)
    epochStart = datetime(2000 + yr, mo, d, h, m, int(s)).timestamp()
    # print(f"Epoch starts at timestamp: {epochStart}")
    if start is None:
        startTime = datetime.fromtimestamp(epochStart)
        startsec = 0
    else:
        startTime = datetime.fromtimestamp(start + epochStart)
        startsec = start + 0

    if end is None:
        endTime = startTime + timedelta(0, orbPeriod * orbPeriods)
        endsec = 0 + orbPeriod * orbPeriods
    elif start is None:
        raise ValueError("If end is given, start can not be none")
    else:
        endTime = datetime.fromtimestamp(end + epochStart)
        endsec = start + 0 + orbPeriod * orbPeriods

    # generate a timeset with start and end and the given dt
    trange = pd.date_range(startTime, endTime, freq=f"{dt}S")
    # time for plot
    timeArray = trange.to_numpy()
    # get julian dates
    t = trange.to_julian_date().to_numpy()
    # split it between decimals and the integer
    jd = np.floor(t).astype(np.int64)
    fr = t - jd

    e, r, v = satellite.sgp4_array(jd, fr)

    # error messages
    if np.any(e) != 0:
        print("Errors in sgp4")
        for error in np.unique(e):
            print(f"code {error}: {SGP4_ERRORS[error]}")

    return t, timeArray, r, v, startsec, endsec, startTime, endTime


# def plotOrbit(
#     t: np.ndarray,
#     r: np.ndarray,
#     v: np.ndarray,
#     dt: float,
#     satName: str,
#     NORADid: int,
#     start: datetime,
#     end: datetime,
#     show: bool = False,
#     saveFile: str = "A0.png",
# ):
#     """plots the carthesian coordinates of position and velocity
#
#     Args:
#         t (np.ndarray): time array
#         r (np.ndarray): carthesian position coordinate
#         v (np.ndarray): carthesian velocity component
#         dt (float): timestep
#         satName (str): satellite name
#         NORADid (int): NORAD id of satellite
#         start (datetime): start time of propagation
#         end (datetime): end time of propagation
#         end (bool): show plot, false by defaultma
#     """
#
#     # start = start.isoformat(sep=" ", timespec="seconds")  # type: ignore
#     # end = end.isoformat(sep=" ", timespec="seconds")  # type: ignore
#     title = f"{satName} | NORAD: {NORADid} | dt = {dt}\n from {start} to {end}"
#
#     fig, axs = plt.subplots(2, 1, sharex=True)
#
#     axs[0].plot(t, r, label=["$r_x$", "$r_y$", "$r_z$"])
#     axs[1].plot(t, v, label=["$v_x$", "$v_y$", "$v_z$"])
#
#     axs[0].legend()
#     axs[1].legend()
#     axs[0].grid()
#     axs[1].grid()
#
#     # axs[0].set_xticks([])
#
#     axs[0].set_ylabel(f"$Position [km]$")
#     axs[1].set_ylabel(f"$Velocity [km/s]$")
#     axs[1].set_xlabel(f"Time [hh:mm]")
#
#     plt.suptitle(title)
#     date_form = DateFormatter("%H:%M")
#     axs[1].xaxis.set_major_formatter(date_form)
#
#     print(f"saving plot to : {saveFile}")
#     fig.savefig(saveFile)
#     if show:
#         plt.show()


# def storeOrbit(t, r, v, filename="orbit.csv", addTimestamp=False):
#     print(f"Storing orbit data to: {filename}")
#     if addTimestamp:
#         timestamp = str(int(datetime.now().timestamp()))
#     else:
#         timestamp = ""
#
#     temp = np.concatenate([r, v], axis=1)
#     P = pd.DataFrame(temp, columns=["rx", "ry", "rz", "vx", "vy", "vz"])
#     P = P.set_index(t)
#     P.to_csv(filename + timestamp)


# def runA0(
#     NORADid: int,
#     nOrbits: int,
#     dt: float,
#     showPlot=False,
#     outputFile="orbit.csv",
#     forceRegen=False,
#     storeOrbitFile=True
# ):
#     """New since last time so i can run it as a module. im so happy i overengineered A0"""
#
#     inputFile = "TLE.dat"
#
#     if not os.path.exists(inputFile) or forceRegen:
#         print("Generating TLE.dat")
#         generateDATFile(NORADid)
#     else:
#         # print("TLE.dat has already been generated")
#         pass
#
#     s, t, satName = retrieveTLEdat(inputFile)
#
#     satellite = Satrec.twoline2rv(s, t)
#
#     JD, time, r, v, start, end, startTime, endTime = propagateSat(
#         satellite, nOrbits, dt=dt
#     )
#
#     if storeOrbitFile:
#         storeOrbit(time, r, v, filename=outputFile)
#
#     if showPlot:
#         plotOrbit(
#             time,
#             r,
#             v,
#             dt,
#             satName=satName,
#             NORADid=NORADid,
#             start=startTime,
#             end=endTime,
#             show=showPlot,
#         )
#
#     return satName, JD, time, r, v, start, end, startTime, endTime
#
#
if __name__ == "__main__":
    TLE1_1, TLE1_2, TLE2_1, TLE2_2 = returnTestTLE()

    generateError(TLE1_1, TLE1_2, TLE2_1, TLE2_2,dt)

    #AssignDF

    # satellite = Satrec.twoline2rv(s, t)
    # JD, time, r, v, _, _, start, end = propagateSat(satellite, nOrbits, dt)

