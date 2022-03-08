from orbital import *
from pprint import pprint

lat, lon, height = 55.3970, 55.3970, 130  # Azimuth spb

path = 'C:/Users/Yarik9008/YandexDisk/Lorett-Rotator/level-up'

#path = '/home/pi/Lorett-Rotator/level-up'

lor_or = Lorett_Orbital('l2s', lon, lat, height, path, timeZone=3)

# Обновление tle-файлов
# print(lor_or.update_tle())

# Определение координат станции по Ip адресу
# print(lor_or.getCoordinatesByIp())

# составление расписания и вывод в виде таблички 
lor_or.getSchedule(52, printTable=True)

# составление расписания и возвращение его в виде списка 
#pprint(lor_or.getSchedule(12, returnScheduleNameSatellite=True))

# составление трека в виде списка 
#pprint(lor_or.nextPasses())

# составление сохранение и отрисовка трека 
# lor_or.nextPasses(printTrack=True, viewPlotTrack=True, savePlotTrack=True)

