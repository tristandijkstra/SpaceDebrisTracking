#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 13:06:08 2022

@author: pieter
"""
"""
NOTE: THIS FILE HAS THE SOLE PURPOSE OF "TRYING" DIFFERENT DEFINITIONS, NOT 
USED FOR FURTHER REPORTING
"""

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


s1 = "1 27386U 02009A   20001.54192287  .00000005  00000-0  15038-4 0  9994"
t1 = "2 27386  98.1404  17.3951 0001257  86.5901  84.8559 14.37967408934480"
s2 = "1 27386U 02009A   20001.82053934  .00000003  00000-0  14345-4 0  9998"
t2 = "2 27386  98.1404  17.6591 0001254  86.7982  86.1169 14.37967399934527"


# satellite1 = Satrec.twoline2rv(s1,t1)
# satellite2 = Satrec.twoline2rv(s2,t2)

# mo1, d1, h1, m1, s1 = days2mdhms(satellite1.epochyr, satellite1.epochdays)
# mo2, d2, h2, m2, s2 = days2mdhms(satellite2.epochyr, satellite2.epochdays)

# jd2, fr2 = jday(satellite2.epochyr + 2000, mo2, d2, h2, m2, s2)

# e1, r1, v1 = satellite1.sgp4(jd2,fr2)
# e2, r2, v2 = satellite2.sgp4(jd2,fr2)

# r1 = np.asarray(r1) #in km
# r2 = np.asarray(r2) #in km

# error = np.absolute(r1-r2)


def generateError(TLE1_1, TLE1_2, TLE2_1, TLE2_2, dt):
    satellite1 = Satrec.twoline2rv(TLE1_1, TLE1_2)
    satellite2 = Satrec.twoline2rv(TLE2_1, TLE2_2)

    mo1, d1, h1, m1, s1 = days2mdhms(satellite1.epochyr, satellite1.epochdays)
    mo2, d2, h2, m2, s2 = days2mdhms(satellite2.epochyr, satellite2.epochdays)

    jd2, fr2 = jday(satellite2.epochyr, mo2, d2, h2, m2, s2)

    e1, r1, v1 = satellite1.sgp4(jd2, fr2)
    e2, r2, v2 = satellite2.sgp4(jd2, fr2)

    # r1 = np.asarray(r1)  # in km
    # r2 = np.asarray(r2)  # in km

    error = np.array(r2) - np.array(r1)  # True value minus calculated value
    magnitude = np.sqrt(np.square(error).sum(axis=0))

    return list(error) + [magnitude]


def AssignDF(file):
    file[["errorX", "errorY", "errorZ", "magnitude"]] = file.apply(
        lambda x: generateError(
            x.TLE_LINE1min1, x.TLE_LINE2min1, x.TLE_LINE1, x.TLE_LINE2, x.deltat
        ),
        axis=1,
        result_type="expand",
    )
    return file

df = pd.read_csv("/Users/pieter/Documents/TU/MSc Spaceflight/Q2/AE4S10 Microsat Engineering/Group Assignment/SpaceDebrisTracking/data/27386.csv")
# df = pd.read_csv("data/2013-066/39416.csv")

a = AssignDF(df)
print(a)
