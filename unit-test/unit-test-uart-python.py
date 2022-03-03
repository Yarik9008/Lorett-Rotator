import serial

DEBUG = False

class PULT_Logging:
    def __init__(self) -> None:
        pass

    def critical(*args):
        pass

    def debug(*args):
        pass

    def warning(*args):
        pass


class Rotator_SerialPort:
    def __init__(self,
                 logger: PULT_Logging = PULT_Logging,
                 port: str = '/dev/ttyS0',
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

    def Receiver_tnpa(self):
        global DEBUG
        '''прием информации с аппарата'''
        data = None

        while data == None or data == b'':
            data = self.serial_port.readline()

        try:
            dataout = str(data)
        except:
            self.logger.warning('Error converting data')
            return None

        if DEBUG:
            self.logger.debug(f'Receiver data : {str(data)}')
        return dataout

    def rotate(self, azimut:float, height:float):
        global DEBUG
        # отправка данных на ардуино
        self.serial_port.write((f'$rotation {azimut} {height};\n').encode())
        if DEBUG:
            self.logger.debug('Send data: ' + f'$rotation {azimut} {height};\n')

test_log = PULT_Logging()
test_pult = Rotator_SerialPort()

if __name__ == '__main__':
    while True:
        a = float(input('az: '))
        h = float(input('he: '))
        test_pult.rotate(a, h)
        print('Report: ' + str(test_pult.Receiver_tnpa()))
        