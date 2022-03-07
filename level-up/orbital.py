# импорт библиотек
from operator import length_hint
from pyorbital.orbital import Orbital
from datetime import datetime, timedelta
from math import radians, tan, sin, cos
from numpy import arange, float32, float64, abs
from requests import get, exceptions
from bs4 import BeautifulSoup as bs
from prettytable import PrettyTable
import matplotlib.pyplot as plt


# TODO сделать фильтрацию по минимальному апогею 
# TODO сделать отрисовку пролетов не только для станций с перемещением облучателя в факальной плоскости 


class Lorett_Orbital():
    def __init__(self, stationName: str,
                 lon: float,
                 lat: float,
                 height: float,
                 path: str,
                 timeZone: int = 0,
                 azimuthCorrection: float = 0) -> None:
        '''Класс для рачета пролетов и простраения треков, также может визуализировать треки.

        In:
            str stationName - название станции

            float lon - долгота

            float lat - широта

            float height - высота над уровнем моря

            str path - расположение папок и скрипта 

            int timeZone - часовой пояс

            float azimuthCorrection - корекция по азимуту'''

        self.version = "0.0.4"
        # масcив станций работающих в l диапазоне по киниматике переноса облучателя в факальной плоскости
        mass_station_l_fokal = ['l2s', 'c4s', 'k4s']
        # массив станций работающих в укв диапазоне
        mass_station_apt = ['lex']
        # массив станций работающих по киниматике полноповоротного перемещения приемной части
        mass_station_rotator = ['r8s']

        # определение типа станции по названию
        if stationName in mass_station_l_fokal:
            self.stationName = stationName
            self.station_type = 'l'
        elif stationName in mass_station_apt:
            self.stationName = stationName
            self.station_type = 'apt'
        elif stationName in mass_station_rotator:
            self.stationName = stationName
            self.station_type = 'rot'

        # координаты станции
        self.lon = round(lon, 5)
        self.lat = round(lat, 5)
        self.height = round(height, 5)
        self.timeZone = timeZone
        # коррекция по азимуту
        self.azimuthCorrection = azimuthCorrection

        # спутники L-диапазона
        self.satList_l = ["NOAA 18",
                          "NOAA 19",
                          "METEOR-M 2",
                          "METEOR-M2 2",
                          "METOP-B",
                          "METOP-C",
                          "FENGYUN 3B",
                          "FENGYUN 3C"]
        # спутники укв диапазона
        self.satList_apt = ["NOAA 18",
                            "NOAA 19",
                            "METEOR-M 2"]

        # конвиг для станций L-диапазона с киниматикой перемещения облучателя в факальной плоскости
        self.config_l_fokal = {'defaultFocus': 0.77,
                               'defaultRadius': 0.55,
                               'defaultHorizon': 55,
                               'minApogee': 65}
        # конфиг для станций с полноповотным механизмом
        self.config_rotator = {'defaultHorizon': 15,
                               'minApogee': 35}
        # конфиг для станций укв диапазона
        self.config_apt = {'defaultHorizon': 15,
                           'minApogee': 20}

        # цвет для визуализации
        self.mirrorCircleColor = '#66ccff'

        # путь для сохранения
        self.path = path

    def _getDays(self, date: datetime) -> int:
        '''Сервисная функция по переводу месяцев в кол-во дней

        In:

            datetime date - дата

        Out:

            int data
        '''
        daysForMonth = [
            0,
            31,     # January
            59,     # February
            90,     # March
            120,    # April
            151,    # May
            181,    # June
            212,    # July
            243,    # August
            273,    # September
            304,    # October
            334,    # November
            365     # December
        ]
        days = date.day
        days += daysForMonth[date.month-1]

        return days

    def sphericalToDecart(self, azimuth: float, elevation: float) -> tuple:
        """Сервисная  функция по переводу из сферичиский координат в декартовые

        In:
                float azimuth (градусы)

                float elevation (градусы)
        Out:
                float x (метры)

                float y (метры)"""

        if elevation == 90:
            return 0, 0

        azimuth = radians((azimuth + self.azimuthCorrection) % 360)
        elevation = radians(elevation)

        y = -(self.config_l_fokal['defaultFocus'] / tan(elevation)) * cos(azimuth)
        x = -(self.config_l_fokal['defaultFocus'] / tan(elevation)) * sin(azimuth)

        return x, y

    def degreesToDegreesAndMinutes(self, azimuth: float, elevation: float) -> tuple:
        """Сервисная функция по переводу углов из градусов а минуты

        In:
                float azimuth (градусы)

                float elevation (градусы)
        Out:
                str azimuth (минуты)

                str elevation (минуты)
        """
        typeAz = type(azimuth)
        if typeAz == float or typeAz == float32 or typeAz == float64:
            minutes = azimuth * 60
            degrees = minutes // 60
            minutes %= 60

            azimuthM = f"{int(degrees):03}:{int(minutes):02}"

        elif typeAz == int:
            azimuthM = f"{azimuth:03}:00"

        else:
            return False

        typeEl = type(elevation)
        if typeEl == float or typeEl == float32 or typeEl == float64:
            minutes = elevation * 60
            degrees = minutes // 60
            minutes %= 60

            elevationM = f"{int(degrees):03}:{int(minutes):02}"

        elif typeEl == int:
            elevationM = f"{elevation:03}:00"

        else:
            return False

        return azimuthM, elevationM

    def update_tle(self) -> bool:
        '''Функция по обнавлению TLE-файлов

        Out:
            bool - статус обнавления '''
        try:
            page = get("http://celestrak.com/NORAD/elements/")
            html = bs(page.content, "html.parser")
            now = datetime.utcnow()

            # Getting TLE date with server
            try:
                year = int(html.select('h3.center')[0].text.split(' ')[3])
                dayPass = int(html.select('h3.center')[
                              0].text.replace(')', '').rsplit(' ', 1)[1])

            except:
                year = now.year
                dayPass = 0

            # Getting TLE date with client
            try:
                name = self.path + "/tle/tle.txt"
                with open(name, "r") as file:
                    yearInTLE, daysPassInTLE = map(
                        int, file.readline().strip().split(' '))

            except:
                yearInTLE = now.year
                daysPassInTLE = 0

            # if TLE is outdated then update TLE
            if (yearInTLE <= year) and (daysPassInTLE < dayPass):

                with open(name, "wb") as file:
                    file.write(
                        f"{now.year} {self._getDays(now)}\n".encode('utf-8'))
                    file.write(
                        get("http://www.celestrak.com/NORAD/elements/weather.txt").content)

        except exceptions.ConnectionError:
            print('Error when update TLE')
            print("No internet connection\n")
            return False

        except Exception as e:
            print('Error when update TLE')
            print(str(e), "\n")
            return False

        return True

    def getCoordinatesByIp(self) -> tuple:
        """Функция для определения координат станции по ip адресу (потенциально не точно)

        Out:
                float lon - долгота

                float lat - широта

                float height - высота над уровнем моря
        """
        try:
            query = get("http://ip-api.com/json").json()

            lon = query['lon']
            lat = query['lat']

            # temporary return only elevation by coordinates
            query = get(
                f'https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}').json()
            alt = query['results'][0]['elevation']

        except exceptions.ConnectionError:
            print('Error when get coordinates')
            print("No internet connection\n")

            return 0, 0, 0

        except Exception as e:
            print('Error when get coordinates')
            print(str(e))

            return 0, 0, 0

        alt /= 1000

        return lon, lat, alt

    def getSatellitePasses(self, start: str, length: int, satellite: str, tol: float = 0.001) -> list:
        """ Функция расчитывающая пролеты спутников

        In:
                str satellite - название спутника

                datetime start - время начала рассчета 

                int length - на сколько часов рассчитать 

                float tol - шаг
        Out:
                datetime start, datetime end, datetime apogee 

                (время начала, время апогея, время окончания)
        """
        nametle = self.path + '/tle/tle.txt'

        orb = Orbital(satellite, nametle)
        if self.station_type == 'l':
            return orb.get_next_passes(start, length, self.lon, self.lat, self.height, tol, self.config_l_fokal['defaultHorizon'])
        elif self.station_type == 'apt':
            return orb.get_next_passes(start, length, self.lon, self.lat, self.height, tol, self.config_apt['defaultHorizon'])
        elif self.station_type == 'rot':
            return orb.get_next_passes(start, length, self.lon, self.lat, self.height, tol, self.config_rotator['defaultHorizon'])

    def getSchedule(self, length: int, tol: float = 0.001, printTable: bool = False, saveSchedule: bool = False, returnTable: bool = False, returnScheduleNameSatellite: bool = False) -> PrettyTable:
        """Функция для составления расписания пролетов

        In:
                int length - продолжительность расчета (часы)

                float tol - шаг

                bool printTable - вывод в виде таблицы

                bool saveSchedule - сохранить табличку

                bool returnTable - вернуть табличку в виде строки

                bool  returnScheduleNameSatellite - вывод в виде списка с названиями спутников 
        Out:
                PrettyTable table - вывод расписания в виде таблички 

                list schedule - возвращает расписание в виде списка картежей
        """

        passes = {}
        allPasses = []
        start = datetime.utcnow()

        th = ["Satellite", "DateTime", "Azimuth", "Elevation"]
        td = []
        passesForReturn = []

        # составление расписания в зависимости от диапазона станции
        if self.station_type == 'l' or self.station_type == 'rot':
            # Iterating through all the passes
            for satellite in self.satList_l:
                pas = self.getSatellitePasses(
                    start, length, satellite, tol=tol)
                # Flights of a specific satellite
                passes[satellite] = pas
                # All passes
                for i in pas:
                    allPasses.append(i)

        elif self.station_type == 'apt':
            # Iterating through all the passes
            for satellite in self.satList_apt:
                pas = self.getSatellitePasses(
                    start, length, satellite, tol=tol)
                # Flights of a specific satellite
                passes[satellite] = pas
                # All passes
                for i in pas:
                    allPasses.append(i)

        # Generate table
        for onePass in sorted(allPasses):
            satName = ''
            if self.station_type == 'l' or self.station_type == 'rot':
                # Going through the list of satellites
                for satellite in self.satList_l:
                    # If the selected span corresponds to a satellite
                    if onePass in passes[satellite]:
                        satName = satellite
                        break
            elif self.station_type == 'apt':
                # Going through the list of satellites
                for satellite in self.satList_l:
                    # If the selected span corresponds to a satellite
                    if onePass in passes[satellite]:
                        satName = satellite
                        break

            name = self.path + '/tle/tle.txt'
            orb = Orbital(satellite, name)

            # расчет в зависимости от типа станций
            if self.station_type == 'l':
                # if apogee > minApogee
                if orb.get_observer_look(onePass[2], self.lon, self.lat, self.height)[1] >= self.config_l_fokal['defaultHorizon']:
                    passesForReturn.append((orb, onePass))
                    td.append([satName, (onePass[0] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"),
                               *map(lambda x: round(x, 2), orb.get_observer_look(onePass[0], self.lon, self.lat, self.height))])
                    td.append([satName, (onePass[2] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"),
                               *map(lambda x: round(x, 2), orb.get_observer_look(onePass[2], self.lon, self.lat, self.height))])
                    td.append([satName, (onePass[1] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"),
                               *map(lambda x: round(x, 2), orb.get_observer_look(onePass[1], self.lon, self.lat, self.height))])
                    td.append([" ", " ", " ", " "])

            elif self.station_type == 'apt':
                # if apogee > minApogee
                if orb.get_observer_look(onePass[2], self.lon, self.lat, self.height)[1] >= self.config_apt['defaultHorizon']:
                    passesForReturn.append((orb, onePass))
                    td.append([satName, (onePass[0] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"),
                               *map(lambda x: round(x, 2), orb.get_observer_look(onePass[0], self.lon, self.lat, self.height))])
                    td.append([satName, (onePass[2] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"),
                               *map(lambda x: round(x, 2), orb.get_observer_look(onePass[2], self.lon, self.lat, self.height))])
                    td.append([satName, (onePass[1] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"),
                               *map(lambda x: round(x, 2), orb.get_observer_look(onePass[1], self.lon, self.lat, self.height))])
                    td.append([" ", " ", " ", " "])
            
            elif self.station_type == 'rot':
                # if apogee > minApogee
                if orb.get_observer_look(onePass[2], self.lon, self.lat, self.height)[1] >= self.config_rotator['defaultHorizon']:
                    passesForReturn.append((orb, onePass))
                    td.append([satName, (onePass[0] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"),
                               *map(lambda x: round(x, 2), orb.get_observer_look(onePass[0], self.lon, self.lat, self.height))])
                    td.append([satName, (onePass[2] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"),
                               *map(lambda x: round(x, 2), orb.get_observer_look(onePass[2], self.lon, self.lat, self.height))])
                    td.append([satName, (onePass[1] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"),
                               *map(lambda x: round(x, 2), orb.get_observer_look(onePass[1], self.lon, self.lat, self.height))])
                    td.append([" ", " ", " ", " "])

        table = PrettyTable(th)

        # Adding rows to tables
        for i in td:
            table.add_row(i)

        start += timedelta(hours=self.timeZone)
        stop = start + timedelta(hours=length) + timedelta(hours=self.timeZone)

        # Generate schedule string
        schedule = f"Satellits Schedule / LorettOrbital {self.version}\n\n"
        schedule += f"Coordinates of the position: {round(self.lon, 4)}° {round(self.lat, 4)}°\n"
        schedule += f"Time zone: UTC {'+' if self.timeZone >= 0 else '-'}{abs(self.timeZone)}:00\n"
        schedule += f"Start: {start.strftime('%Y.%m.%d %H:%M:%S')}\n"
        schedule += f"Stop:  {stop.strftime('%Y.%m.%d %H:%M:%S')}\n"

        if self.station_type == 'l':
            schedule += f"Minimum Elevation: {self.config_l_fokal['defaultHorizon']}°\n"
            schedule += f"Minimum Apogee: {self.config_l_fokal['minApogee']}°\n"

        elif self.station_type == 'apt':
            schedule += f"Minimum Elevation: {self.config_apt['defaultHorizon']}°\n"
            schedule += f"Minimum Apogee: {self.config_apt['minApogee']}°\n"
        
        elif self.station_type == 'rot':
            schedule += f"Minimum Elevation: {self.config_rotator['defaultHorizon']}°\n"
            schedule += f"Minimum Apogee: {self.config_rotator['minApogee']}°\n"

        schedule += f"Number of passes: {len(td)//4}\n\n"
        schedule += table.get_string()

        if printTable:
            print()
            print(schedule)

        if saveSchedule:
            try:
                name = self.path + '/schedule/Schedule_' + \
                    '-'.join('-'.join('-'.join(str(datetime.now()
                                                   ).split()).split('.')).split(':')) + '.txt'
                with open(name, 'w') as file:
                    file.write(schedule)

            except Exception as e:
                print("ERROR:", e)
                return None

        if returnTable:
            return schedule
        elif returnScheduleNameSatellite:
            massout = []
            for pas in passesForReturn:
                massout.append((pas[0].satellite_name, pas[1]))
            return massout
        else:
            return passesForReturn

    def generateTrack(self, satellite: str, satPass: list, viewPlotTrack: bool = False, savePlotTrack: bool = False):
        """Функция для генерирования трек файла для L2s
        In:
                str satellite - название спутника

                list satPass - следующий пролет 

                bool viewPlotTrack - отображение визуализации трека 

                bool  savePlotTrack - сохранение визуализации трека
        Out:
                tuple (название спутника [время, азимут, высота]) - трек для отслеживания спутника 

        """
        nametle = self.path + "/tle/tle.txt"

        orb = Orbital(satellite, nametle)

        nametrack = self.path + \
            f"/tracks/{satellite.replace(' ', '-')}_L2S_{satPass[0].strftime('%Y-%m-%dT%H-%M')}.txt"

        with open(nametrack, "w") as file:

            times = []
            coordsX = []
            coordsY = []
            sphCoordsAZ = []
            sphCoordsEL = []

            startTime = satPass[0].strftime('%Y-%m-%d   %H:%M:%S') + " UTC"

            metaData = f"Link2Space track file / LorettOrbital {self.version}\n" +     \
                       f"StationName: {self.stationName}\n" +                       \
                       f"Station Position: {self.lon}\t{self.lat}\t{self.height}\n" +  \
                       f"Satellite: {satellite}\n" +                                \
                       f"Start date & time: {startTime}\n" +                        \
                       f"Orbit: {orb.get_orbit_number(satPass[0])}\n" +             \
                       "Time(UTC)\t\tAzimuth(d)\tElevation(d) X(m)\t\tY(m)\n\n"

            # Write metadata
            file.write(metaData)

            # Generating track steps
            for i in range((satPass[1] - satPass[0]).seconds):

                dateTimeForCalc = satPass[0] + timedelta(seconds=i)
                strTime = dateTimeForCalc.strftime("%H:%M:%S")

                # Convert degrees to degrees:minutes
                observerLook = orb.get_observer_look(
                    dateTimeForCalc, self.lon, self.lat, self.height)

                sphCoords = self.degreesToDegreesAndMinutes(*observerLook)

                # Convert degrees to Cartesian coords for create a plot
                coords = self.sphericalToDecart(*observerLook)

                times.append(strTime)
                coordsX.append(coords[0])
                coordsY.append(coords[1])
                sphCoordsAZ.append(sphCoords[0])
                sphCoordsEL.append(sphCoords[1])

                string = f"{strTime}   {sphCoords[0]}   {sphCoords[1]}\n"
                file.write(string)


        if viewPlotTrack or savePlotTrack:
            self.SavePlotTrack(coordsX, coordsY, satellite=satellite, start=startTime,
                                       viewPlotTrack=viewPlotTrack, savePlotTrack=savePlotTrack)

        return satellite, list(zip(times, sphCoordsAZ, sphCoordsEL))

    def SavePlotTrack(self, coordsX: list, coordsY: list, satellite: str = "Untitled", start: str = "", viewPlotTrack: bool = False, savePlotTrack: bool = False) -> None:
        """Функция для отрисовки трека и сохренения его в файл (работает только для стануий с перемещением облучателя в фокальной плоскости)
        In:
                float coordsX[] - массив координат по оси х

                float coordsY[] - массив координат по оси у

                str satellite - название спутника

                str start - время начала пролета

                bool viewPlotTrack - отрисовка и вывод картинки трека без сохранения 

                bool savePlotTrack - сохранение визуализации трека 

                bool printTrack - вывод трека в консоль 
        Out:
                None
        """

        if (viewPlotTrack or savePlotTrack) and self.station_type == 'l':
            ax = plt.gca()
            ax.set_aspect('equal', adjustable='box')

            # Plot mirror
            circle = plt.Circle((0, 0), self.config_l_fokal['defaultRadius'],
                                color=self.mirrorCircleColor)
            ax.add_patch(circle)

            # Set window title
            fig = plt.figure(1)
            fig.canvas.manager.set_window_title(satellite + "   " + start)

            # Generate OX and OY Axes
            steps = list(round(i, 1) for i in arange(
                -self.config_l_fokal['defaultRadius'], self.config_l_fokal['defaultRadius'] + 0.1, 0.1))

            plt.title(satellite + "   " + start)

            # Plot OX and OY Axes
            plt.plot([0]*len(steps), steps, '--k')
            plt.plot(steps, [0]*len(steps), '--k')

            # Plot track
            plt.plot(coordsX, coordsY, '-.r')

            # Plot start and end points
            plt.plot(coordsX[0], coordsY[0], ".b")
            plt.plot(coordsX[-1], coordsY[-1], ".r")

            # Plot north
            plt.plot(0, self.config_l_fokal['defaultRadius'], "^r")

            if savePlotTrack:
                fileName = self.path + \
                    f"/tracksSchemes/TracksSchemes_{satellite.replace(' ', '-')}_{start.replace('   ', '-').replace(':', '-')}.png"
                plt.savefig(fileName)

            if viewPlotTrack:
                plt.show()
        else:
            print("\033[31m {}" .format('Format is not recognized'))
            return None

    def setCoordinates(self, lon: float, lat: float, height: float) -> None:
        '''Функция для установки местоположения станции

        In:

            float lon - долгота

            float lat - широта

            float height - высота над уровнем моря'''

        self.lon = round(lon, 5)
        self.lat = round(lat, 5)
        self.height = round(height, 5)

    def nextPasses(self, printTrack: bool = False, viewPlotTrack: bool = False, savePlotTrack: bool = False):
        '''Функция для расчета трека ближайщего следующего пролета

        In:
            bool  printTrack - вывод трека в консоль

            bool viewPlotTrack - отображение визуализации трека 

            bool  savePlotTrack - сохранение визуализации трека

        Out:
            tuple (название спутника [время, азимут, высота]) - трек для отслеживания спутника'''

        length = 12

        passesList = self.getSchedule(length, printTable=False)

        count = 1
        td = []

        for satPass, satPasTimeList in passesList:

            td.append([count, satPass.satellite_name, *satPasTimeList, round(
                satPass.get_observer_look(satPasTimeList[2], self.lon, self.lat, self.height)[1], 2)])
            td.append(("", "", "", "", "", ""))

            count += 1

        satPass, satPasTimeList = passesList[0]

        if self.station_type == 'l' or self.station_type == 'rot':
            outTrack =  self.generateTrack(satPass.satellite_name, satPasTimeList, viewPlotTrack=viewPlotTrack,  savePlotTrack=savePlotTrack)

            if printTrack:
                print('         ',outTrack[0])
                for stepp in outTrack[1]:
                    print(stepp[0], stepp[1], stepp[2], sep='   ')

            return outTrack
        else:
            print("\033[31m {}" .format('Format is not recognized'))
            return None
