from sgp4.api import Satrec, SGP4_ERRORS
import pandas as pd
import numpy as np
import time
from warnings import warn
from typing import Tuple


def generateErrors(
    TLE_LINE1: str, TLE_LINE2: str, TLE_LINE1min1: str, TLE_LINE2min1: str
) -> Tuple[float, float, float, float]:
    """generate the TLE covariance errors for x, y, z and the overall covariance

    Args:
        TLE_LINE1 (str): the first line of the current TLE
        TLE_LINE2 (str): the second line of the current TLE
        TLE_LINE1min1 (str): the first line of the previous TLE
        TLE_LINE2min1 (str): the second line of the previous TLE

    Returns:
        Tuple[float, float, float, float]: errorX, errorY, errorZ, overallPositionCovariance
    """
    sat = Satrec.twoline2rv(TLE_LINE1, TLE_LINE2)
    satmin1 = Satrec.twoline2rv(TLE_LINE1min1, TLE_LINE2min1)

    epoch = sat.jdsatepoch
    epochfr = sat.jdsatepochF

    e, r, v = sat.sgp4(epoch, epochfr)
    emin1, rmin1, vmin1 = satmin1.sgp4(epoch, epochfr)

    if np.any([e, emin1]) != 0:
        print("Warning: Error in SGP4", end="")
        for error in np.unique(e):
            print(f"code {error}: {SGP4_ERRORS[error]}", end="")
        print("")
        return None, None, None, None  # type: ignore

    else:
        positionError = np.array(r) - np.array(rmin1)
        # velocityError = np.array(v) - np.array(vmin1)
        positionOverallCovariance = np.sqrt(np.sum(np.square(positionError)))

        return (
            positionError[0],
            positionError[1],
            positionError[2],
            positionOverallCovariance,
        )


def testAssign(file):
    # this is just to test, do not use
    warn(DeprecationWarning("testAssign is just to test, do not use"))
    # file = file.apply(
    file[["errorX", "errorY", "errorZ", "magnitude"]] = file.apply(
        lambda x: generateErrors(
            x.TLE_LINE1, x.TLE_LINE2, x.TLE_LINE1min1, x.TLE_LINE2min1
        ),
        axis=1,
        result_type="expand",
    )
    return file


if __name__ == "__main__":
    # tests
    TLE_LINE1 = "1 39416U 13066A   16002.76110523 +.00000398 +00000-0 +54149-4 0  9990"
    TLE_LINE2 = "2 39416 097.7110 067.5703 0041210 195.3492 164.6476 14.83425137114401"
    TLE_LINE1min1 = "1 39416U 13066A   16001.81675900  .00000428  00000-0  57846-4 0  9991"
    TLE_LINE2min1 = "2 39416  97.7111  66.6585 0041130 198.4629 161.5095 14.83424384114290"


    errorsTest = generateErrors(TLE_LINE1, TLE_LINE2, TLE_LINE1min1, TLE_LINE2min1)
    # (0.016149681323440745, 0.055385587249475066, 0.02879765662344574, 0.06448007838720261)
    print(errorsTest)
    testCSV = pd.read_csv(r"data/2013-066/39416.csv")
    start = time.perf_counter()
    testCSV = testAssign(testCSV)
    end = time.perf_counter()

    print(testCSV)
    print(f"Time: {end - start}")
    print(f"Time example: {(end - start) * 75}")
