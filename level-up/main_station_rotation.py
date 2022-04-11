from datetime import timedelta
from os import name
from sched import scheduler
from HardwareLorettRotator import *
from lorettOrbital.orbital import *
from threading import Thread
from pprint import pprint
from time import sleep

simulat = True

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
            config['horizon'] = 15
            config['minApogee'] = 40
            self.orbital = Scheduler(self.stationName, self.lat, self.lon, self.alt, self.path, timeZone=self.timeZone, config=config)

            self.logger.info('start lorettOrbital.Scheduler')
        except:
            self.logger.error('no start lorettOrbital.Scheduler')
        
        try:
            port = list(filter(lambda x: '' in x, map(str, list_ports.comports())))[0].split(' - ')[0]
            #port = 'COM19'
            self.rotator = Rotator_SerialPort(self.logger, DEBUG=True, port=port)
            #self.rotator.homing()
            self.logger.info('start Rotator_SerialPort')
        except:
            self.logger.error('no start Rotator_SerialPort')


        self.schedule += self.orbital.getSchedule(24, returnNameSatellite=True)
        pprint(self.schedule)

    def tracking(self,track:tuple, simulation=False):
        '''Функция для отслеживания спутника во время пролета'''
        self.logger.info(f'start tracking satellite {track[0]}')

        self.logger.debug(f"Go to start pozition: az: {track[1][0][1]} el: {track[1][0][2]}")
        self.rotator.rotate(track[1][0][1], track[1][0][2])
        sleep(5)
        """
        while self.rotator.feedback() != "OK":
            pass
        """
        for steps in track[1][1:]:
            self.logger.debug(f'Go to pozitions: az: {steps[1]} el: {steps[2]}')
            self.rotator.rotate(steps[1], steps[2])
            sleep(1)
  





    def sleep_to_next(self, time_sleep:datetime, nameSatellite:str):
        time_sleep = int(time_sleep.total_seconds())
        self.logger.info(f'Next satellite {nameSatellite} pass to: {time_sleep} seconds')
        while time_sleep > 70:
            sleep(10)
            time_sleep -= 10
            self.logger.debug(f'Next satellite {nameSatellite} pass to: {time_sleep} seconds')
        while time_sleep > 1:
            sleep(1)
            time_sleep -= 1
            self.logger.debug(f'Next satellite {nameSatellite} pass to: {time_sleep} seconds')
        
            
    def main(self):
        while True:
            
            input('press any key..')
            # берем следующий пролет
            satPas = self.schedule[0]
            self.schedule = self.schedule[1:]
            # вычисляем время до пролета 
            sleep_time = satPas[1][0] - datetime.utcnow() - timedelta(seconds=5)
            if not simulat:
                self.sleep_to_next(sleep_time, satPas)

            # 
            # s[0])
            self.tracking(self.orbital.nextPass())
            self.rotator.homing()

if __name__ == '__main__':
    station = Main_Lorett_Rotator()
    station.main()