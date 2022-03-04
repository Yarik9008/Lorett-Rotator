from sympy import im
from lorettorbital.orbital import Station
from datetime import datetime
from pprint import pprint


if __name__ == "__main__":
    station = Station("testStation", 55.55, 37.36, 0.180)
    station.findPasses(datetime.utcnow())

    pprint(station.getStation(), indent=4)

