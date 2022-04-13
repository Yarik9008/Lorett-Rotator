from cmath import isnan
from datetime import timedelta
from tkinter.tix import Tree
from HardwareLorettRotator import *
from lorettOrbital.orbital import *
from pprint import pprint
from time import sleep



def isNumber(num : str):
    isNum = True
    try:
        float(num)
    except ValueError:
        isNum = False
    return isNum 

class Main_Lorett_Rotator:
    '''Класс адаптер для организации взаимодействия между отдельными компонентами'''

    def __init__(self) -> None:

        self.stationName = 'r8s'

        #self.path = 'C:/Users/Yarik9008/YandexDisk/Lorett-Rotator/level-up'
        self.path = '/home/pi/Lorett-Rotator/level-up'

        self.lat = 54.52678
        self.lon = 36.16776
        self.alt = 0.160
        self.timeZone = 3

        self.schedule = []

        self.logger = LorettLogging(self.path)
        
        try:
            config = supportedStationTypes['r8s'].copy()
            config['horizon'] = 70
            config['minApogee'] = 80
            self.orbital = Scheduler(self.stationName, self.lat, self.lon, self.alt, self.path, timeZone=self.timeZone, config=config)

            self.logger.info('start lorettOrbital.Scheduler')
        except Exception as e:
            print(e)
            self.logger.error('no start lorettOrbital.Scheduler')

        try:
            port = list(filter(lambda x: 'ACM' in x, map(str, list_ports.comports())))[0].split(' - ')[0]
            #port = '/dev/ttyACM6'
            #port = 'COM18'
            self.rotator = Rotator_SerialPort(self.logger, DEBUG=True, port=port)
            #self.rotator.homing()
            self.logger.info('start Rotator_SerialPort')
        except:
            self.logger.error('no start Rotator_SerialPort')


        self.schedule += self.orbital.getSchedule(24, returnNameSatellite=True)
        pprint(self.schedule)

    def tracking(self, track, wait, simulation=False):
        '''Функция для отслеживания спутника во время пролета'''
        self.logger.info(f'start tracking satellite {track[0]}')

        self.logger.debug(f"Go to start pozition: az: {track[1][0][1]} el: {track[1][0][2]}")
        self.rotator.navigate(track[1][0][1], track[1][0][2])
        
        #self.sleep_to_next(wait - datetime.utcnow(), track[0])

        """
        for steps in track[1][1:]:
            self.logger.debug(f'Go to pozition: az: {steps[1]} el: {steps[2]}')
            if (track)
            self.rotator.navigate(steps[1], steps[2], False)
            sleep(1 if not simulation else 0.5)
        """
        for i in range(1, len(track[1])):
            self.logger.debug(f'Go to pozition: az: {track[1][i][1]} el: {track[1][i][2]}')

            self.rotator.navigate(track[1][i][1], track[1][i][2], False)
            sleep(1 if not simulation else 0.5)

        #FIXIT
        """
        for i in range(1, len(track[1])):
            speed = abs(track[1][i][1] - track[1][i-1][1])
            self.logger.debug(f'Go to pozition: az: {track[1][i][1]} el: {track[1][i][2]} with speed {speed} deg/s')
            self.rotator.navigateDynamic(track[1][i][1], track[1][i][2], speed)
            sleep(0.5)# if not simulation else 0.5)
            """
        self.rotator.comeBack()
        


    def sleep_to_next(self, time_sleep:datetime, nameSatellite:str):
        time_sleep = int(time_sleep.total_seconds())
        self.logger.info(f'Next satellite {nameSatellite[0]} pass to: {time_sleep} seconds')
        while time_sleep > 60:
            sleep(10)
            time_sleep -= 10
            self.logger.debug(f'Next satellite {nameSatellite[0]} pass to: {time_sleep} seconds')
        while time_sleep > 1:
            sleep(1)
            time_sleep -= 1
            self.logger.debug(f'Next satellite {nameSatellite[0]} pass to: {time_sleep} seconds')


    def main(self):
        self.logger.info(f'First calibration started')
        self.rotator.navigate(0, 25, True)
        self.rotator.goHome()
        
        command = ''

        while True:
            command = input("Home correction: ").split()

            if command[0] == 'save':
                self.rotator.saveCorrection()
                break
            
            elif command[0] == 'end':
                self.rotator.clearCorrection()
                break
        
            #FIXIT
            if len(command) == 2:
                if isNumber(command[0]) and isNumber(command[1]):
                    azimuth = abs(float(command[0])) % 360
                    elevation = abs(float(command[1])) % 91

                    if float(command[0]) < 0:
                        azimuth *= -1
                    if float(command[1]) < 0:
                        elevation *= -1

                    self.rotator.navigateRel(azimuth, elevation, corrections=True)        
        
        while True:
            self.rotator.navigate(0, 90)

            # берем следующий пролет
            satPas = self.schedule[0]
            self.schedule = self.schedule[1:]

            # вычисляем время до пролета
            sleep_time = satPas[1][0] - datetime.utcnow() - timedelta(seconds=15)
            #self.sleep_to_next(sleep_time, satPas)
            #sleep(20)
            track = self.orbital.nextPass()
            track = (track[0], [[i[0], float(i[1]), float(i[2])]  for i in track[1]])

            self.tracking(track, satPas[1][0])
            self.rotator.goHome()

if __name__ == '__main__':
    station = Main_Lorett_Rotator()
    station.main()
