from tabnanny import check
import matplotlib.pyplot as plt

from pyorbital.orbital import Orbital
from datetime import datetime, timedelta
from math import radians, tan, sin, cos
from numpy import arange, float32, float64, abs
from prettytable import PrettyTable

from os import getcwd
from os.path import abspath, join, dirname, isfile
from pathlib import Path

###
from requests import get, exceptions
from bs4 import BeautifulSoup as bs

from Exceptions import *

check_apt = True


__all__ = [
    "Station"
    "satList",
    "version"
]

# For calculate the number of days since the beginning of the year (leap years are not taken into account)
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

if check_apt:
    # dict for run with argv
    satList = ["NOAA 18",
                "NOAA 19",
                "METEOR-M 2"]
else:
    # dict for run with argv
    satList = ["NOAA 18",
                "NOAA 19",
                "METEOR-M 2",
                "METEOR-M2 2",
                "METOP-B",
                "METOP-C",
                "FENGYUN 3B",
                "FENGYUN 3C"]

version = "0.0.3"


# Should I use the current cwd directory to store TLE and tracks or save him in library path
# Later, it will be possible to configure it normally
useCwd = False
root = abspath(getcwd()) if useCwd else abspath(dirname(__file__))

# additional directories
tlePath = join( root, "tle" )
Path( tlePath ).mkdir(parents=True, exist_ok=True)

tracksPath = join( root, "tracks" )
Path( tracksPath ).mkdir(parents=True, exist_ok=True)

tracksSchemesPath = join( root, "tracksSchemes" )
Path( tracksSchemesPath ).mkdir(parents=True, exist_ok=True)

# mirror specifications
defaultFocus = 0.77
defaultRadius = 0.55
defaultHorizon = 15
minApogee = 20
azimuthCorrection = 0

# colors
mirrorCircleColor = '#66ccff'

# list of supported Track formats
trackFormats = [
    "l2s",
    "c4s"
]


# Main Station Class
class Station:
    def __init__(self, stationName: str, lon: float = None, lat: float = None, alt: float = None, timeZone: int = 0,
                 mirrorFocus: float = defaultFocus, mirrorRadius: float = defaultRadius, mirrorHorizon: float = defaultHorizon,
                 minApogee: float = minApogee, azimuthCorrection: float = azimuthCorrection, satList: list = satList, trackFormat: str = trackFormats[1]) -> None:

        self.stationName = stationName

        if all((lat, lon, alt)):
            self.lon = round(lon, 5)
            self.lat = round(lat, 5)
            self.alt = round(alt, 5)

        else:
            self.lon = lon
            self.lat = lat
            self.alt = alt

        self.timeZone = timeZone

        self.mirrorFocus = mirrorFocus
        self.mirrorRadius = mirrorRadius
        self.mirrorHorizon = mirrorHorizon
        self.minApogee = minApogee
        self.azimuthCorrection = azimuthCorrection

        self.mirrorCircleColor = mirrorCircleColor

        self.satList = satList
        self.trackFormat = trackFormat

        self._createSubDirectories()


    def _findSatteliteNameInTLE(self, sattelite) -> None:
        satList = []
        with open(join(self.tlePath, 'tle.txt')) as f:
            satList = f.readlines()[1::3]

        if sattelite in satList:
            return True

        maxid = -1
        maxx = -1
        for i in range(len(satList)):
            ratio = fuzz.ratio(sattelite, satList[i])
            if ratio > maxx:
                maxx = ratio
                maxid = i

        print("Sattilite not found in TLE.")

        if maxx > 80:
            print("Maybe you mean {0}".format(satList[maxid]))

        return False



        # мб добавить неявное сравнение строк, чтобы предлогать подсказку вида "maybe you meen ..."


    def _checkCoordinates(self) -> None:
        """
        Service function for checking coordinates before calculate
        """
        if not all((self.lon, self.lat, self.alt)):
            raise CoordinatesAreNotGiven(self.lon, self.lon, self.lat)

        if any((abs(self.lon) > 90, abs(self.lat) > 90)):
            raise InvalidCoordinates


    def _createSubDirectories(self) -> None:
        """
        Service function that creates the necessary work for the directory
        """

        self.tlePath = join( root, "tle" )
        Path( tlePath ).mkdir(parents=True, exist_ok=True)

        self.tracksPath = join( root, "tracks" )
        Path( tracksPath ).mkdir(parents=True, exist_ok=True)

        self.tracksSchemesPath = join( root, "tracksSchemes" )
        Path( tracksSchemesPath ).mkdir(parents=True, exist_ok=True)


    def _getDays(self, date: datetime) -> int:
        """
        Service function that calculates count days since the biginning of the year

        In:
                datetime date

        Out:
                int deys
        """

        days = date.day
        days += daysForMonth[ date.month-1 ]

        return days


    def sphericalToDecart(self, azimuth: float, elevation: float) -> tuple:
        """
        Function that translates coordinates from the spherical to the Cartesian coordinate system (a, e) --> (x, y)

        (The central reflection is taken into account)

        In:
                float azimuth

                float elevation

                ( In degrees )


        Out:
                float x

                float y

                ( In meters )
        """

        # tan(90') does not exist, at this moment the satellite is at the zenith above us
        if elevation == 90:
            return 0, 0

        azimuth = radians( (azimuth + self.azimuthCorrection) % 360 )
        elevation = radians(elevation)


        y = -(self.mirrorFocus / tan(elevation)) * cos(azimuth)
        x = -(self.mirrorFocus / tan(elevation)) * sin(azimuth)

        return x, y


    def degreesToDegreesAndMinutes(self, azimuth: float, elevation: float) -> tuple:
        """
        A function that translates angular coordinates to the form degrees:minutes (a, e) --> (a:m, e:m)

        In:
                float azimuth

                float elevation

                ( In degrees )


        Out:
                str azimuth:minutes

                str elevation:minutes


        Returns False if incorrect data is given
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


    def update(self, showLog: bool = True) -> None:
        """
        Function that updates TLE files

        In:
                bool showLog
        """

        try:
            if showLog:
                print("Connecting to celestrak.com\n")

            page = get( "http://celestrak.com/NORAD/elements/" )
            html = bs(page.content, "html.parser")
            now = datetime.utcnow()


            # Getting TLE date with server
            try:
                year = int(html.select('h3.center')[0].text.split(' ')[3])
                dayPass = int(html.select('h3.center')[0].text.replace(')', '').rsplit(' ', 1)[1])

            except:
                year = now.year
                dayPass = 0

            if showLog:
                print("On site:")
                print(year, dayPass, end='\n\n')

            # Getting TLE date with client
            try:
                with open( join( tlePath, "tle.txt" ), "r" ) as file:
                    yearInTLE, daysPassInTLE = map(int, file.readline().strip().split(' '))

            except:
                yearInTLE = now.year
                daysPassInTLE = 0

            if showLog:
                print("In TLE:")
                print(yearInTLE, daysPassInTLE, end='\n\n')


            # if TLE is outdated then update TLE
            if (yearInTLE <= year) and (daysPassInTLE < dayPass):
                if showLog:
                    print("Update TLE..\n")

                with open( join( tlePath, "tle.txt" ), "wb" ) as file:
                    file.write( f"{now.year} {self._getDays(now)}\n".encode('utf-8') )
                    file.write(get("http://www.celestrak.com/NORAD/elements/weather.txt").content)

                if showLog:
                    print("Done")

            else:
                if showLog:
                    print("TLE are Relevant")

        except exceptions.ConnectionError:
            print('Error when update TLE')
            print("No internet connection\n")

        except Exception as e:
            print('Error when update TLE')
            print(str(e), "\n")



    def getCoordinatesByIp(self) -> tuple:
        """
        Function that gets the station coordinates by his ip.

        Returned Altitude in kilometers.\n\n

        ATTENTION!

        THESE COORDINATES MAY BE VERY INACCURATE.

        USE IT ONLY FOR MAKING AN APPROXIMATE SCHEDULE.\n\n


        Out:
                float lon

                float lat

                float alt


        If there is an error:
                float lon=None

                float lat=None

                float alt=None

        """

        try:
            print( "Get coordinates by IP.." )
            query = get("http://ip-api.com/json").json()

            lon = query['lon']
            lat = query['lat']

            # temporary return only elevation by coordinates
            query = get(f'https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}').json()
            alt = query['results'][0]['elevation']

        except exceptions.ConnectionError:
            print('Error when get coordinates')
            print("No internet connection\n")

            lon = None
            lat = None
            alt = None

        except Exception as e:
            print('Error when get coordinates')
            print(str(e))

            lon = None
            lat = None
            alt = None

        print(f"Youre coordinates: {lon} {lat} {alt}m\n")
        alt/=1000

        self.lon = lon
        self.lat = lat
        self.alt = alt

        return lon, lat, alt


    # rename isUpdateTLE
    def getSatellitePasses(self, start: str, length: int, satellite: str, tol: float = 0.001, updateTLE: bool = True) -> list:
        """
        Function that calculates satellite passes by input parametres

        In:
                str satellite

                datetime start

                int length

                float tol

                bool updateTLE

        Out:
                datetime start, datetime end, datetime apogee
        """
        self._checkCoordinates()

        if updateTLE:
            self.update(showLog=False)

        orb = Orbital(satellite, join( self.tlePath, "tle.txt" ) )

        return orb.get_next_passes(start, length, self.lon, self.lat, self.alt, tol, self.mirrorHorizon)


    def getSchedule(self, start: datetime, length: int, tol: float = 0.001, printTable: bool = True,  output: str = "",  updateTLE: bool = True) -> PrettyTable:
        """
        Function that makes up the schedule, according to the parameters.

        In:

                str output

                datetime start

                int length

                float tol

                bool printTable

                bool updateTLE

        Out:
                PrettyTable table

        Saves the schedule in "output" and prints it if necessary.

        Not the best implementation but there is no other one yet.

        It does not take into account time zone curves, since I am too lazy to saw the implementation for the sake of several points of the planet
        """
        self._checkCoordinates()

        if updateTLE:
            self.update(showLog=False)

        passes = {}
        allPasses = []

        th = ["Satellite", "DateTime", "Azimuth", "Elevation"]
        td = []

        passesForReturn = []

        # Iterating through all the passes
        for satellite in self.satList:
            pas = self.getSatellitePasses(start, length, satellite, tol = tol)

            # Flights of a specific satellite
            passes[satellite] = pas

            # All passes
            for i in pas:
                allPasses.append(i)

        # Generate table
        for onePass in sorted(allPasses):
            satName = ''

            # Going through the list of satellites
            for satellite in satList:
                # If the selected span corresponds to a satellite
                if onePass in passes[satellite]:
                    satName = satellite
                    break

            orb = Orbital(satellite, join( tlePath, "tle.txt" ) )


            # if apogee > minApogee
            if orb.get_observer_look(onePass[2], self.lon, self.lat, self.alt)[1] >= self.minApogee:
                passesForReturn.append((orb, onePass))
                td.append([satName, (onePass[0] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"), *map( lambda x: round(x, 2), orb.get_observer_look(onePass[0], self.lon, self.lat, self.alt)) ])
                td.append([satName, (onePass[2] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"), *map( lambda x: round(x, 2), orb.get_observer_look(onePass[2], self.lon, self.lat, self.alt)) ])
                td.append([satName, (onePass[1] + timedelta(hours=self.timeZone)).strftime("%Y.%m.%d %H:%M:%S"), *map( lambda x: round(x, 2), orb.get_observer_look(onePass[1], self.lon, self.lat, self.alt)) ])
                td.append([" ", " ", " ", " "])

        table = PrettyTable(th)

        # Adding rows to tables
        for i in td:
            table.add_row(i)

        start += timedelta(hours=self.timeZone)
        stop = start + timedelta(hours=length) + timedelta(hours=self.timeZone)

        # Generate schedule string
        schedule = f"Satellits Schedule / LorettOrbital {version}\n\n"
        schedule += f"Coordinates of the position: {round(self.lon, 4)}° {round(self.lat, 4)}°\n"
        schedule += f"Time zone: UTC {'+' if self.timeZone >= 0 else '-'}{abs(self.timeZone)}:00\n"
        schedule += f"Start: {start.strftime('%Y.%m.%d %H:%M:%S')}\n"
        schedule += f"Stop:  {stop.strftime('%Y.%m.%d %H:%M:%S')}\n"
        schedule += f"Minimum Elevation: {self.mirrorHorizon}°\n"
        schedule += f"Minimum Apogee: {self.minApogee}°\n"
        schedule += f"Number of passes: {len(td)//4}\n\n"
        schedule += table.get_string()

        if printTable:
            print()
            print(schedule)

        if output != "":
            try:
                with open(output, 'w') as file:
                    file.write(schedule)

            except Exception as e:
                print("ERROR:", e)

        return passesForReturn


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
            ax=plt.gca()
            ax.set_aspect('equal', adjustable='box')

            Path( join(currentPath, "tracksSchemes") ).mkdir(parents=True, exist_ok=True)

            # Plot mirror
            circle = plt.Circle((0, 0), self.mirrorRadius, color=self.mirrorCircleColor)
            ax.add_patch(circle)

            # Set window title
            fig = plt.figure(1)
            fig.canvas.manager.set_window_title(satellite + "   " + start)

            # Generate OX and OY Axes
            steps = list(round(i, 1) for i in arange(-self.mirrorRadius, self.mirrorRadius + 0.1, 0.1))

            plt.title(satellite + "   " + start)

            # Plot OX and OY Axes
            plt.plot( [0]*len(steps), steps, '--k' )
            plt.plot( steps, [0]*len(steps), '--k' )

            # Plot track
            plt.plot(coordsX, coordsY, '-.r')

            # Plot start and end points
            plt.plot( coordsX[0], coordsY[0], ".b")
            plt.plot( coordsX[-1], coordsY[-1], ".r")

            # Plot north
            plt.plot( 0, self.mirrorRadius, "^r")

            if save:
                fileName = f"{satellite.replace(' ', '-')}_{start.replace('   ', '-').replace(':', '-')}.png"
                plt.savefig( join(currentPath, "tracksSchemes", fileName) )

            if show:
                plt.show()


    def getCoordsWithC4STrack(self, filePath: str, currentPath: str, printTrack: bool = False, saveTrack: bool = True):

        """
        Function that reads coordinates from the track-file Copter4Space.

        In:
                str filePath

                bool printTrack

                bool saveTrack


        Out:
                str times[]

                float coordsX[]

                float coordsY[]
        """

        times = []
        coordsX = []
        coordsY = []

        # Let's imagine that this is a "dirty" call
        #lines = open(filePath).readlines()

        with open(filePath) as file:
            lines = file.readlines()

        satellite = lines[0].split(" ", 1)[1].strip()
        startTime = lines[1].split(":", 1)[1].strip().replace("   ", " ")

        lines = lines[6:]

        print("Time:", "X:", "Y:", sep="\t\t")

        # Reading track steps
        for i in lines:
            strTime, azimuth, elevation, x, y = i.strip().split("\t\t")

            times.append(strTime)
            coordsX.append(float(x))
            coordsY.append(float(y))

            print(strTime, x, y, sep="\t\t")

        if printTrack or saveTrack:
            self.printAndSavePlotTrack(coordsX, coordsY, satellite=satellite, start=startTime, currentPath=currentPath, show=printTrack, save=saveTrack)

        return times, coordsX, coordsY


    def getCoordsWithL2STrack(self, filePath: str, currentPath: str, printTrack: bool = False, saveTrack: bool = True):

        """
        Function that reads coordinates from the track-file Link2Space.

        In:
                str filePath

                bool printTrack

                bool saveTrack


        Out:
                str times[]

                float coordsX[]

                float coordsY[]
        """
        times = []
        coordsX = []
        coordsY = []

        # Let's imagine that this is a "dirty" call
        #lines = open(filePath).readlines()

        with open(filePath) as file:
            lines = file.readlines()

        satellite = lines[0].split(" ", 1)[1].strip()
        startTime = lines[1].split(":", 1)[1].strip().replace("   ", " ")

        lines = lines[6:]

        # Reading track steps
        for i in lines:
            strTime, azimuth, elevation = i.split("   ")

            # Convert degrees:minutes to degrees
            azimuth = round(float(azimuth.split(":")[0]) + float(azimuth.split(":")[1])/60, 2)
            elevation = round(float(elevation.split(":")[0]) + float(elevation.split(":")[1])/60, 2)

            # Convert degrees to Cartesian coords
            coords = self.sphericalToDecart(azimuth, elevation)

            times.append(strTime)
            coordsX.append(coords[0])
            coordsY.append(coords[1])

            string = '{}\t\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{:.2f}\n'.format(strTime, azimuth, elevation, coords[0], coords[1])
            print(string, sep="\t\t", end="")

        if printTrack or saveTrack:
            self.printAndSavePlotTrack(coordsX, coordsY, satellite=satellite, start=startTime, currentPath=currentPath, show=printTrack, save=saveTrack)

        return times, coordsX, coordsY


    def generateC4STrack(self, satellite: str, satPass: list, currentPath: str, printTrack: bool = False, saveTrack: bool = True, updateTLE: bool = True):
        """
        Function that generates the track-file Copter4Space.

        In:
                str satellite

                list satPass

                bool printTrack

                bool saveTrack

                bool updateTLE


        Out:
                str times[]

                float coordsX[]

                float coordsY[]
        """
        self._checkCoordinates()

        if updateTLE:
            self.update(showLog=False)

        orb = Orbital(satellite, join( tlePath, "tle.txt" ) )

        Path( join(currentPath, "tracks") ).mkdir(parents=True, exist_ok=True)

        fileName = f"{satellite.replace(' ', '-')}_C4S_{satPass[0].strftime('%Y-%m-%dT%H-%M')}.txt"

        with open( join(currentPath, "tracks", fileName), "w") as file:

            print( "Pass duration:")
            print( str((satPass[1]-satPass[0])).rsplit('.', 1)[0] )

            times = []
            coordsX = []
            coordsY = []

            startTime = satPass[0].strftime('%Y-%m-%d   %H:%M:%S') + " UTC"

            apogeeX, apogeeY = map(lambda pos: round(pos, 3), self.sphericalToDecart(*orb.get_observer_look(satPass[2], self.lon, self.lat, self.alt)))

            metaData = f"Copter4Space track file / LorettOrbital {version}\n" +     \
                       f"StationName: {self.stationName}\n" +                       \
                       f"Station Position: {self.lon}\t{self.lat}\t{self.alt}\n" +  \
                       f"Satellite: {satellite}\n" +                                \
                       f"Start date & time: {startTime}\n" +                        \
                       f"Orbit: {orb.get_orbit_number(satPass[0])}\n" +             \
                       f"Apogee Coordinates:\n" +                                   \
                       f"{apogeeX}\t{apogeeY}\n" +                                  \
                       "Time(UTC)\t\tAzimuth(d)\tElevation(d) X(m)\t\tY(m)\n\n"

            # Write metadata
            file.write(metaData)

            print(metaData)

            # Generating track steps
            for i in range((satPass[1] - satPass[0]).seconds):

                dateTimeForCalc = satPass[0] + timedelta(seconds=i)
                strTime = dateTimeForCalc.strftime("%H:%M:%S")

                # Convert degrees to Cartesian coords
                sphCoords = orb.get_observer_look(dateTimeForCalc, self.lon, self.lat, self.alt)
                coords = self.sphericalToDecart(*sphCoords)

                times.append(strTime)
                coordsX.append(coords[0])
                coordsY.append(coords[1])

                string = '{}\t\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{:.2f}\n'.format(strTime, sphCoords[0], sphCoords[1], coords[0], coords[1])
                file.write(string)

                print(string, end="")


        if printTrack or saveTrack:
            self.printAndSavePlotTrack(coordsX, coordsY, satellite=satellite, start=startTime, currentPath=currentPath, show=printTrack, save=saveTrack)

        return times, coordsX, coordsY


    def generateL2STrack(self, satellite: str, satPass: list, currentPath: str, printTrack: bool = False, saveTrack: bool = True, updateTLE: bool = True):
        """
        Function that generates the track-file Link2Space.

        In:
                str satellite

                list satPass

                bool printTrack

                bool saveTrack

                bool updateTLE


        Out:
                str times[]

                str azimuth:minutes[]

                str elevation:minutes[]
        """
        self._checkCoordinates()

        if updateTLE:
            self.update(showLog=False)

        orb = Orbital(satellite, join( tlePath, "tle.txt" ) )

        Path( join(currentPath, "tracks") ).mkdir(parents=True, exist_ok=True)

        fileName = f"{satellite.replace(' ', '-')}_L2S_{satPass[0].strftime('%Y-%m-%dT%H-%M')}.txt"

        with open( join(currentPath, "tracks", fileName), "w") as file:

            print( "Pass duration:")
            print( str((satPass[1]-satPass[0])).rsplit('.', 1)[0] )

            times = []
            coordsX = []
            coordsY = []
            sphCoordsAZ = []
            sphCoordsEL = []

            startTime = satPass[0].strftime('%Y-%m-%d   %H:%M:%S') + " UTC"

            metaData = f"Link2Space track file / LorettOrbital {version}\n" +     \
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
                observerLook =  orb.get_observer_look(dateTimeForCalc, self.lon, self.lat, self.alt)

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
            self.printAndSavePlotTrack(coordsX, coordsY, satellite=satellite, start=startTime, currentPath=currentPath, show=printTrack, save=saveTrack)

        return times, sphCoordsAZ, sphCoordsEL


    # Maybe there will be another more convenient format
    def generateNeboscopeTrack(satellite, satPass, printTrack=True, saveTrack=True):
        ...

    def getCoordsWithNeboscopeTrack(filePath, printTrack=True, saveTrack=True):
        ...

    def convertL2SToC4STrack():
        ...

    def convertC4SToL2STrack():
        ...


    def setCoordinates(self, lon: float, lat: float, alt: float) -> None:
        self.lon = round(lon, 5)
        self.lat = round(lat, 5)
        self.alt = round(alt, 5)

        self._checkCoordinates()


    def setMirror(self, mirrorFocus: float, mirrorRadius: float, mirrorHorizon: float, minApogee: float = 65, mirrorCircleColor: str = mirrorCircleColor) -> None:
        if mirrorFocus < 0 or mirrorRadius < 0 or mirrorHorizon < 0 or minApogee < 0:
            raise InvalidMirrorParameters(mirrorFocus, mirrorRadius, mirrorHorizon, minApogee)

        self.mirrorFocus = mirrorFocus
        self.mirrorRadius = mirrorRadius
        self.mirrorHorizon = mirrorHorizon
        self.minApogee = minApogee

        self.mirrorCircleColor = mirrorCircleColor


    def setMinApogee(self, minApogee: float) -> None:
        if minApogee < 0:
            raise InvalidMirrorParameters(minApogee=minApogee)

        self.minApogee = minApogee


    def setTimeZone(self, timeZone: int) -> None:
        if abs(timeZone) > 12:
            raise InvalidTimeCorrection

        self.timeZone = timeZone


    def setSatteliteList(self, satteliteList: list):
        satList = []
        for sat in satteliteList:
            if self._findSatteliteNameInTLE(sat):
                satList.append(sat)

        self.satList = satList


    def getStation(self):
        return {"stationName": self.stationName,
                "stationType": self.trackFormat,

                "lon": self.lon,
                "lat": self.lat,
                "alt": self.alt,

                "mirrorFocus": self.mirrorFocus,
                "mirrorRadius": self.mirrorRadius,
                "mirrorHorizon": self.mirrorHorizon,
                "minApogee": self.minApogee,
                "azimuthCorrection": self.azimuthCorrection}


    def getCoordinates(self):
        return {"lon": self.lon,
                "lat": self.lat,
                "alt": self.alt}


    def getMirror(self):
        return {"mirrorFocus": self.mirrorFocus,
                "mirrorRadius": self.mirrorRadius,
                "mirrorHorizon": self.mirrorHorizon,
                "minApogee": self.minApogee,
                "azimuthCorrection": self.azimuthCorrection}


    def getSatteliteList(self):
        return self.satList


    def findPasses(self, start: datetime, length: int = 30, currentPath: str = "", printTrack: bool = False, saveTrack: bool = True):
        passesList = self.getSchedule(start, length, printTable=False)

        print(f"Passes by {length} of hours starting from {start.strftime('%d.%m.%Y %H:%M:%S')} for {', '.join(self.satList)}\n")
        print("UTC time now:", datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S"), end="\n\n")

        count = 1

        self.update(showLog=False)

        # Print satellite passes in the format:
        # UTC time is used!
        # 1. datetime start         datetime end         datetime apogee    apogee elevation
        print("UTC time is used here!\n")

        th = ["№", "Sattelite", "Start", "Stop", "Apogee", "Apogee elevation"]
        td = []

        for satPass, satPasTimeList in passesList:

            td.append([count, satPass.satellite_name, *satPasTimeList, round(satPass.get_observer_look(satPasTimeList[2], self.lon, self.lat, self.alt)[1], 2)])
            td.append(("", "", "", "", "", ""))

            count+=1

        table = PrettyTable(th)
        for i in td:
            table.add_row(i)

        print(table.get_string())

        # console track generator
        if input("\nCreate track-file ? (y/n) ").lower() == "y":

            number = int( input("Enter pass number: ") )-1

            while number >= len(passesList):
                print("Invalid pass number, try again.. ")
                number = int( input("Enter pass number: ") )-1

            satPass, satPasTimeList = passesList[number]
            print()

            if self.trackFormat == "l2s":
                self.generateL2STrack(satPass.satellite_name, satPasTimeList, currentPath=currentPath, saveTrack=saveTrack, printTrack=printTrack)

            elif self.trackFormat == "c4s":
                self.generateC4STrack(satPass.satellite_name, satPasTimeList, currentPath=currentPath, saveTrack=saveTrack, printTrack=printTrack)

            else:
                print("Format is not recognized")


