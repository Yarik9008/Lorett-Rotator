from serial.tools import list_ports
import serial


choosen_port = ''
connection = ''
if __name__ == '__main__':
    port_list = [str(elem) for elem in list_ports.comports()]
    print(*port_list, sep='\n')
    if choosen_port:
        connection = serial.Serial(choosen_port, 9600)
if connection:
    data = str(connection.readline())[2:-5]
