# импорт библиотек
from pyorbital.orbital import Orbital
from datetime import datetime, timedelta
from math import radians, tan, sin, cos
from numpy import arange, float32, float64, abs
from requests import get, exceptions
from bs4 import BeautifulSoup as bs
from prettytable import PrettyTable
import matplotlib.pyplot as plt
#from HardwareLorettRotator import LorettLogging


class Lorett_Orbital():
    def __init__(self, stationName: str,
                 lon: float,
                 lat: float,
                 height: float = 0,
                 timeZone: int = 0,
                 azimuthCorrection:float = 0) -> None:
        '''stationName - название станции, lon - долгота, lat - широта, height - высота над уровнем моря, timeZone - часовой пояс '''
        self.version = "0.0.4"
        # масиив станций работающих в l диапазоне 
        mass_station_l_bend =  ['l2s', 'c4s', 'k4s']
        # массив станций работающих в укв диапазоне 
        mass_station_apt_bend = ['lex']
       

        if stationName in mass_station_l_bend :
            self.stationName = stationName
            self.station_bend = 'l'
        elif stationName in mass_station_apt_bend:
            self.stationName = stationName
            self.station_bend = 'apt'
        
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
        # конвиг для станций L-диапазона
        self.config_l = {'defaultFocus': 0.77,
                         'defaultRadius': 0.55,
                         'defaultHorizon': 55,
                         'minApogee': 65}
        # конфиг для станций укв диапазона
        self.config_apt = {'defaultHorizon': 15,
                           'minApogee': 20}

    def _getDays(self, date: datetime) -> int:
        '''Сервисная функция по переводу месяцев в кол-во дней'''
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

        y = -(self.mirrorFocus / tan(elevation)) * cos(azimuth)
        x = -(self.mirrorFocus / tan(elevation)) * sin(azimuth)

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
        '''Функция по обнавлению TLE-файлов'''
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
                with open("level-up/tle/tle.txt", "r") as file:
                    yearInTLE, daysPassInTLE = map(
                        int, file.readline().strip().split(' '))

            except:
                yearInTLE = now.year
                daysPassInTLE = 0

            # if TLE is outdated then update TLE
            if (yearInTLE <= year) and (daysPassInTLE < dayPass):

                with open('level-up/tle/tle.txt', "wb") as file:
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
                float lon

                float lat

                float alt
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

                время начала, время апогея, время окончания
        """

        orb = Orbital(satellite, "level-up/tle/tle.txt")
        if self.station_bend == 'l':
            return orb.get_next_passes(start, length, self.lon, self.lat, self.height, tol, self.config_l['defaultHorizon'])
        elif self.station_bend == 'apt':
            return orb.get_next_passes(start, length, self.lon, self.lat, self.height, tol, self.config_apt['defaultHorizon'])
    
    def getSchedule(self, start: datetime, length: int, tol: float = 0.001, printTable: bool = True, saveSchedule: bool = False, savePath: str = '') -> PrettyTable:
        """Функция для составления расписания пролетов 
        In:
                datetime start  - время старта расчета 

                int length - продолжительность расчета (часы)

                float tol - шаг

                bool printTable - вывод в виде таблицы

                bool saveSchedule - сохранить табличку

                str savePath - путь для сохранения расписания 
                
        Out:
                PrettyTable table - вывод расписания в виде таблички 

                list schedule - возвращает расписание в виде списка картежей
        """

        passes = {}
        allPasses = []

        th = ["Satellite", "DateTime", "Azimuth", "Elevation"]
        td = []
        passesForReturn = []

        if self.station_bend == 'l':
            # Iterating through all the passes
            for satellite in self.satList_l:
                pas = self.getSatellitePasses(start, length, satellite, tol=tol)
                # Flights of a specific satellite
                passes[satellite] = pas
                # All passes
                for i in pas:
                    allPasses.append(i)

        elif self.station_bend == 'apt':
            # Iterating through all the passes
            for satellite in self.satList_apt:
                pas = self.getSatellitePasses(start, length, satellite, tol=tol)
                # Flights of a specific satellite
                passes[satellite] = pas
                # All passes
                for i in pas:
                    allPasses.append(i)
        
        # Generate table
        for onePass in sorted(allPasses):
            satName = ''
            if self.station_bend == 'l':
                # Going through the list of satellites
                for satellite in self.satList_l:
                    # If the selected span corresponds to a satellite
                    if onePass in passes[satellite]:
                        satName = satellite
                        break
            elif self.station_bend == 'apt':
                # Going through the list of satellites
                for satellite in self.satList_l:
                    # If the selected span corresponds to a satellite
                    if onePass in passes[satellite]:
                        satName = satellite
                        break

            orb = Orbital(satellite, 'level-up/tle/tle.txt')
            if self.station_bend == 'l':
                # if apogee > minApogee
                if orb.get_observer_look(onePass[2], self.lon, self.lat, self.height)[1] >= self.config_l['defaultHorizon']:
                    passesForReturn.append((orb, onePass))
                    td.append([satName, (onePass[0] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"),
                            *map(lambda x: round(x, 2), orb.get_observer_look(onePass[0], self.lon, self.lat, self.height))])
                    td.append([satName, (onePass[2] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"),
                            *map(lambda x: round(x, 2), orb.get_observer_look(onePass[2], self.lon, self.lat, self.height))])
                    td.append([satName, (onePass[1] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"),
                            *map(lambda x: round(x, 2), orb.get_observer_look(onePass[1], self.lon, self.lat, self.height))])
                    td.append([" ", " ", " ", " "])
            elif self.station_bend == 'apt':
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

        if self.station_bend == 'l':
            schedule += f"Minimum Elevation: {self.config_l['defaultHorizon']}°\n"
            schedule += f"Minimum Apogee: {self.config_l['minApogee']}°\n"
        elif self.station_bend == 'apt':
            schedule += f"Minimum Elevation: {self.config_apt['defaultHorizon']}°\n"
            schedule += f"Minimum Apogee: {self.config_apt['minApogee']}°\n"

        schedule += f"Number of passes: {len(td)//4}\n\n"
        schedule += table.get_string()

        if printTable:
            print()
            print(schedule)

        if saveSchedule:
            try:
                with open(savePath + 'Schedule.txt', 'w') as file:
                    file.write(schedule)

            except Exception as e:
                print("ERROR:", e)

        return passesForReturn

    def generateL2STrack(self, satellite: str, satPass: list, currentPath: str, printTrack: bool = False, saveTrack: bool = True):
        """Функция для генерирования трек файла для L2s
        In:
                str satellite - название спутника

                list satPass - следующий пролет

                bool printTrack - вывод трека в пролет 

                bool saveTrack - сохранение трека 
        Out:
                str times[] - время

                str azimuth:minutes[] - азимут

                str elevation:minutes[] - высота 

        """

        orb = Orbital(satellite, "level-up/tle/tle.txt")

        fileName = f"{satellite.replace(' ', '-')}_L2S_{satPass[0].strftime('%Y-%m-%dT%H-%M')}.txt"

        with open(currentPath + "tracks" + fileName, "w") as file:

            print("Pass duration:")
            print(str((satPass[1]-satPass[0])).rsplit('.', 1)[0])

            times = []
            coordsX = []
            coordsY = []
            sphCoordsAZ = []
            sphCoordsEL = []

            startTime = satPass[0].strftime('%Y-%m-%d   %H:%M:%S') + " UTC"

            metaData = f"Link2Space track file / LorettOrbital {self.version}\n" +     \
                       f"StationName: {self.stationName}\n" +                       \
                       f"Station Position: {self.lon}\t{self.lat}\t{self.alt}\n" +  \
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
                    dateTimeForCalc, self.lon, self.lat, self.alt)

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

                print(string, end="")

        if printTrack or saveTrack:
            self.printAndSavePlotTrack(coordsX, coordsY, satellite=satellite, start=startTime,
                                       currentPath=currentPath, show=printTrack, save=saveTrack)

        return times, sphCoordsAZ, sphCoordsEL

    def printAndSavePlotTrack(self, coordsX: list, coordsY: list, satellite: str = "Untitled", start: str = "", currentPath: str = "", save: bool = True, show: bool = False) -> None:
        """
        Function that draws the path of the irradiator on the pyplot scheme

        In:
                float coordsX[]

                float coordsY[]

                str satellite

                str start

                str currentPath

                bool save

                bool show

        Out:
                None
        """

        if save or show:
            ax = plt.gca()
            ax.set_aspect('equal', adjustable='box')

            # Plot mirror
            circle = plt.Circle((0, 0), self.mirrorRadius,
                                color=self.mirrorCircleColor)
            ax.add_patch(circle)

            # Set window title
            fig = plt.figure(1)
            fig.canvas.manager.set_window_title(satellite + "   " + start)

            # Generate OX and OY Axes
            steps = list(
                round(i, 1) for i in arange(-self.mirrorRadius, self.mirrorRadius + 0.1, 0.1))

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
            plt.plot(0, self.mirrorRadius, "^r")

            if save:
                fileName = f"{satellite.replace(' ', '-')}_{start.replace('   ', '-').replace(':', '-')}.png"
                plt.savefig(currentPath +  "tracksSchemes" + fileName)

            if show:
                plt.show()


    def generateNeboscopeTrack(satellite, satPass, printTrack=True, saveTrack=True):
        pass

    def getCoordsWithNeboscopeTrack(filePath, printTrack=True, saveTrack=True):
        pass

    def setCoordinates(self, lon: float, lat: float, alt: float) -> None:
        self.lon = round(lon, 5)
        self.lat = round(lat, 5)
        self.height = round(alt, 5)

    def findPasses(self, start: datetime, length: int = 30, currentPath: str = "", printTrack: bool = False, saveTrack: bool = True):

        passesList = self.getSchedule(start, length, printTable=False)
        print(passesList)
        count = 1
        td = []

        for satPass, satPasTimeList in passesList:

            td.append([count, satPass.satellite_name, *satPasTimeList, 
            round(satPass.get_observer_look(satPasTimeList[2], self.lon, self.lat, self.height)[1], 2)])
            td.append(("", "", "", "", "", ""))

            count += 1

        number = 1

        while number >= len(passesList):  
            satPass, satPasTimeList = passesList[number]
            if self.station_bend == 'l':
                self.generateL2STrack(satPass.satellite_name, satPasTimeList, currentPath=currentPath, saveTrack=saveTrack, printTrack=printTrack)
            # elif self.trackFormat == "c4s":
            #     self.generateC4STrack(satPass.satellite_name, satPasTimeList,
            #                           currentPath=currentPath, saveTrack=saveTrack, printTrack=printTrack)
            else:
                print("Format is not recognized")
