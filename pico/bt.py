import struct

from machine import UART, Pin

def _parse_float(uart_reads):
    return float(b"".join(uart_reads))

class BluetoothCommunication:
    # states:
    #
    #   -> header 11111111
    # 0 -> curr x
    # 1 -> curr y
    # 2 -> pred x
    # 3 -> pred y
    # 4 -> goal x
    # 5 -> goal y

    def __init__(self, uart, tx, rx, key, baudrate=9600, master=True, slave_addr=None) -> None:
        self._uart = UART(uart, baudrate=baudrate, tx=Pin(tx), rx=Pin(rx))
        self._key = Pin(key, mode=Pin.OUT)

        self._master = master
        self._slave_addr = slave_addr

        self._configure_chip()

        self._counter = 0
        self._curr_float = []
        self._ready = False
        self._started = False

        self._curr_x = 0
        self._curr_y = 0
        self._pred_x = 0
        self._pred_y = 0
        self._goal_x = 0
        self._goal_y = 0

        self._reading = {
            "curr_x": 0,
            "curr_y": 0,
            "pred_x": 0,
            "pred_y": 0,
            "goal_x": 0,
            "goal_y": 0,
        }
    
    def _configure_chip(self):
        # enter configuration mode
        self._key.high()

        # clear any paired devices
        self._uart.write('AT+RMAAD')

        # configure baudrate
        self._uart.write('AT+UART=38400,0,0')

        # connect if master
        if self._master:
            # set as master
            self._uart.write('AT+ROLE=1')

            # connect

            # set connection mode
            self._uart.write('AT+CMODE=0')

            # set connection address
            connection_cmd = 'AT+BIND=' + str(self._slave_addr)
            self._uart.write(connection_cmd)

            # configure baudrate
            pass
        else:
            # set as slave
            self._uart.write('AT+ROLE=0')

            # clear the buffer
            self._uart.read()

            # get the address and print it out
            self._uart.write('AT+ADDR')
            addr = self._uart.read()
            print("Bluetooth address:")
            print(addr)
        
        self._key.low()

    def tick_read(self):
        read = self._uart.read(1)

        if read == b'11111111':
            self._counter = 0
            self._curr_float = []
            self._started = True
        
        if self._started:
            self._curr_float.append(read)
        else:
            return

        if len(self._curr_float) == 4:
            # ready to parse a float
            curr_float = _parse_float(self._curr_float)
            if self._counter == 0:
                self._curr_x = curr_float
            elif self._counter == 1:
                self._curr_y = curr_float
            elif self._counter == 2:
                self._pred_x = curr_float
            elif self._counter == 3:
                self._pred_y = curr_float
            elif self._counter == 4:
                self._goal_x = curr_float
            elif self._counter == 5:
                self._goal_y = curr_float
                self._ready = True
                self._started = False
                self._update_reading()
            
            self._counter += 1
            self._curr_float = []

    def _update_reading(self):
        self._reading = {
            "curr_x": self._curr_x,
            "curr_y": self._curr_y,
            "pred_x": self._pred_x,
            "pred_y": self._pred_y,
            "goal_x": self._goal_x,
            "goal_y": self._goal_x,
        }
    
    def get_reading(self):
        if self._ready:
            return self._reading
    
    def transmit_state(self, reading):
        # header
        self._uart.write(b'11111111')

        # data
        self._uart.write(reading['curr_x'])
        self._uart.write(reading['curr_y'])
        self._uart.write(reading['pred_x'])
        self._uart.write(reading['pred_y'])
        self._uart.write(reading['goal_x'])
        self._uart.write(reading['goal_y'])
    
    def is_ready(self):
        return self._ready
