import serial
from serial.tools import list_ports


class Rotator_SerialPort:
    def __init__(self,
                 logger: PULT_Logging = PULT_Logging,
                 port: str = str = list(filter(lambda x: 'ACM' in x, map(str, list_ports.comports())))[0].split(' - ')[0],
                 bitrate: int = 9600
                 ):
        global DEBUG
        # инициализация переменных
        self.check_connect = False
        self.logger = logger
        # открытие порта 
        self.serial_port = serial.Serial(
            port=port,
            baudrate=bitrate,
            timeout=0.1)
    
    def rotate(self, azimut:float, height:float):
        '''Поворот антенны на определенный угол'''
        global DEBUG
        # отправка данных на ардуино
        self.serial_port.write((f'$rotation {azimut} {height};\n').encode())
        if DEBUG:
            self.logger.debug('Send data: ' + f'$rotation {azimut} {height};\n')
        if self.feedback() == 'OK':
            return 'OK'
        else:
            return 'ERROR'

    def homing(self):
        ''' обнуление антенны по концевикам'''
        global DEBUG
        # отправка данных на ардуино
        self.serial_port.write((f'$homing;\n').encode())
        if DEBUG:
            self.logger.debug('Send data: $homing;\n')
        if self.feedback() == 'OK':
            return 'OK'
        else:
            return 'ERROR'


    def feedback(self):
        global DEBUG
        '''прием информации с аппарата'''
        while data == None or data == b'':
            data = self.serial_port.readline()
        try:
            dataout = str(data)[2:-1]
        except:
            self.logger.warning('Error converting data')
            return 'ERROR'
        return dataout