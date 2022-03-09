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
                 port: str = list(filter(lambda x: 'ACM' in x, map(str, list_ports.comports())))[0].split(' - ')[0],
                 bitrate: int = 9600,
                 DEBUG: bool = False
                 ):

        # list(filter(lambda x: 'ACM' in x, map(str, list_ports.comports())))[0].split(' - ')[0]

        self.DEBUG = DEBUG
        # инициализация переменных
        self.check_connect = False
        self.logger = logger
        # открытие порта 
        self.serial_port = serial.Serial(
            port=port,
            baudrate=bitrate,
            timeout=0.1)
    
    def rotate(self, azimut:str, height:str):

        height = str(float('.'.join(str(azimut).split(':'))))
        azimut = 0
        # = str(float('.'.join(str(height).split(':'))))
        print(f'$rotation {azimut} {height};\n')
        '''Поворот антенны на определенный угол'''
        # отправка данных на ардуино
        self.serial_port.write((f'$rotation {azimut} {height};\n').encode())
        if self.DEBUG:
            self.logger.debug('Send data: ' + f'$rotation {azimut} {height};\n')
        #if self.feedback() == 'OK':
            return True
        else:
            return False

    def homing(self):
        ''' обнуление антенны по концевикам'''
        # отправка данных на ардуино
        self.serial_port.write((f'$homing;\n').encode())
        if self.DEBUG:
            self.logger.debug('Send data: $homing;\n')
        #if self.feedback() == 'OK':
            return True
        else:
            return False


    def feedback(self):
        '''прием информации с аппарата'''
        while data == None or data == b'':
            data = self.serial_port.readline()
        try:
            dataout = str(data)[2:-1]
        except:
            self.logger.warning('Error converting data')
            return None
        return dataout