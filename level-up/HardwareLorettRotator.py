from time import sleep
import serial
import logging
from serial.tools import list_ports
from datetime import datetime
import coloredlogs


class LorettLogging:
    '''Класс отвечающий за логирование. Логи пишуться в файл, так же выводться в консоль'''
    def __init__(self, path: str):
        self.mylogs = logging.getLogger(__name__)
        self.mylogs.setLevel(logging.DEBUG)

        # обработчик записи в лог-файл
        name = path + '/log/' + \
            '-'.join('-'.join('-'.join(str(datetime.now()).split()
                                       ).split('.')).split(':')) + '.log'

        self.file = logging.FileHandler(name)
        self.fileformat = logging.Formatter(
            "%(asctime)s:%(levelname)s:%(message)s")

        self.file.setLevel(logging.DEBUG)
        self.file.setFormatter(self.fileformat)

        # обработчик вывода в консоль лог файла
        self.stream = logging.StreamHandler()
        self.streamformat = logging.Formatter(
            "%(levelname)s:%(module)s:%(message)s")

        self.stream.setLevel(logging.DEBUG)
        self.stream.setFormatter(self.streamformat)

        # инициализация обработчиков
        self.mylogs.addHandler(self.file)
        self.mylogs.addHandler(self.stream)

        coloredlogs.install(level=logging.DEBUG, logger=self.mylogs,
                            fmt='%(asctime)s [%(levelname)s] - %(message)s')

        self.mylogs.info('start-logging')


    def debug(self, message):
        '''сообщения отладочного уровня'''
        self.mylogs.debug(message)


    def info(self, message):
        '''сообщения информационного уровня'''
        self.mylogs.info(message)


    def warning(self, message):
        '''не критичные ошибки'''
        self.mylogs.warning(message)


    def critical(self, message):
        '''мы почти тонем'''
        self.mylogs.critical(message)


    def error(self, message):
        '''ребята я сваливаю ща рванет !!!!'''
        self.mylogs.error(message)


class Rotator_SerialPort:
    '''Класс для взаимодействия с низкоуровневой частью приемного комплекса'''

    def __init__(self,
                 logger: LorettLogging,
                 port: str = '',
                 bitrate: int = 57600,
                 DEBUG: bool = False
                 ):

        #port = list(filter(lambda x: 'ACM' in x, map(str, list_ports.comports())))[0].split(' - ')[0]

        self.DEBUG = DEBUG

        self.check_connect = False
        self.logger = logger

        # открытие порта
        self.serial_port = serial.Serial(
            port=port,
            baudrate=bitrate,
            timeout=0.1)


    def navigate(self, azimut:float, elevation:float, fast=True):
        '''Поворот антенны на определенный угол'''
        try:
            if fast:
                self.serial_port.write((f'$nf {azimut} {elevation};\n').encode())
                if self.DEBUG:
                    self.logger.debug('Send data: ' + f'$nf {azimut} {elevation};\n')
            else: 
                self.serial_port.write((f'$n {azimut} {elevation};\n').encode())
                if self.DEBUG:
                    self.logger.debug('Send data: ' + f'$n {azimut} {elevation};\n')

            data = ''
            while data != 'OK':
                data = str(self.feedback())[:-5]
            
            return True

        except:
            return False

    def navigateDynamic(self, azimut : float, elevation : float, speed : float):
        '''Поворот антенны на определенный угол'''
        try:
            self.serial_port.write((f'$nd {azimut} {elevation} {speed};\n').encode())
            if self.DEBUG:
                self.logger.debug(f'Send data: $nd {azimut} {elevation} {speed};\n')

            data = ''
            while data != 'OK':
                data = str(self.feedback())[:-5]
            
            return True

        except:
            return False

    def navigateRel(self, azimut:float, elevation:float, corrections=False):
        '''Поворот антенны на определенный угол относительно текущего положения'''
        try:
            if corrections:
                self.serial_port.write((f'$nrc {azimut} {elevation};\n').encode())

                if self.DEBUG:
                    self.logger.debug('Send data: ' + f'$nrc {azimut} {elevation};\n')
                    
            else:
                self.serial_port.write((f'$nr {azimut} {elevation};\n').encode())

                if self.DEBUG:
                    self.logger.debug('Send data: ' + f'$nr {azimut} {elevation};\n')                

            data = ''
            while data != 'OK':
                data = str(self.feedback())[:-5]

            return True

        except:
            return False

    def comeBack(self):
        '''Поворот антенны на определенный угол'''
        try:
            self.serial_port.write((f'$cb;\n').encode())
            if self.DEBUG:
                self.logger.debug(f'Send data: $cb;\n')

            data = ''
            while data != 'OK':
                data = str(self.feedback())[:-5]
            
            return True

        except:
            return False

    def goHome(self):
        ''' обнуление антенны по концевикам'''
        try:
            # отправка данных на ардуино
            data = '$h;\n'
            print('go home')
            self.serial_port.write(data.encode())

            if self.DEBUG:
                self.logger.debug(f'Send data: {data}')

            data = ''
            while data != 'OK':
                data = str(self.feedback())[:-5]

            print('end home')

            return True
            
        except:
            return False

    def saveCorrection(self):
        try:
            self.serial_port.write(f'$s;\n'.encode())
            self.logger.info('Save correction position')

            return True

        except:
            self.logger.error('Error save correction position')  

            return False

    def clearCorrection(self):
        try:
            self.serial_port.write(f'$c;\n'.encode())
            self.logger.info('Clear correction position')

            return True

        except:
            self.logger.error('Error clear correction position')  

            return False
    

    def feedback(self):
        '''прием информации с аппарата'''
        data = None
        while data == None or data == b'':
            data = self.serial_port.readline()

        try:
            dataout = str(data)[2:]

        except:
            self.logger.warning('Error converting data')
            return None

        return dataout
