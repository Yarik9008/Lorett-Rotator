from sqlalchemy import false
from orbital import Station
from pprint import pprint
from datetime import datetime, timedelta


# coordinates of the patriot Park
lat, lon, alt = 55.3970, 43.8302, 130  # Azimuth spb

# if you want to use your current coordinates (determined by the ip address)
#lon, lat, alt = getCoords()

# m --> km
alt /= 1000

# start time in UTC
start = datetime.utcnow()

station = Station("testStation", lon, lat, alt, timeZone=3, trackFormat="l2s")

pprint(station.getStation(), indent=4)


print("\n")
name = 'NOAA 19'
Path = 'C:/Users/lynx9/Desktop/'

station.findPasses(start,30,Path,printTrack=False)

