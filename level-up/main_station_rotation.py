from HardwareLorettRotator import *
from orbital import *

class Main_Lorett_Rotator:
    '''Класс адаптер для организации взаимодействия между отдельными компонентами'''

    def __init__(self) -> None:

        self.stationName = 'l2s' 

        self.path = 'C:/Users/lynx9/YandexDisk/Lorett-Rotator/level-up'
        #self.path = '/home/pi/Lorett-Rotator/level-up'

        self.lat = 55.3970
        self.lon = 55.3970
        self.height = 130 
        self.timeZone = 3

        self.logger = LorettLogging(self.path)
        try:
            self.orbital = Lorett_Orbital(self.stationName, self.lon, self.lat, self.height, self.path, timeZone=self.timeZone)
            self.logger.info('start Lorett_Orbital')
        except:
            self.logger.error('no start Lorett_Orbital')
        
        try:
            self.rotator = Rotator_SerialPort(self.logger)
            self.logger.info('start Rotator_SerialPort')
        except:
            self.logger.error('no start Rotator_SerialPort')


if __name__ == '__main__':
    station = Main_Lorett_Rotator()