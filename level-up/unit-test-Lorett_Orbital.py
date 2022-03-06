from re import T
from orbital import *
from pprint import pprint

lat, lon, height = 55.3970, 43.8302, 130  # Azimuth spb
start = datetime.now()
lor_or = Lorett_Orbital('l2s',lon, lat, height, timeZone=3)
# Обновление tle-файлов
#print(lor_or.update_tle())
# Определение координат станции по Ip адресу
#print(lor_or.getCoordinatesByIp())
# составление расписания 
#print(lor_or.getSchedule(start, 48, saveSchedule=True, printTable=False))
pprint(lor_or.findPasses())