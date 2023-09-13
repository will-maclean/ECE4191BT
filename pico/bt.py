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

        self.counter = 0
        self.curr_float = []
        self.ready = False

        self.curr_x = 0
        self.curr_y = 0
        self.pred_x = 0
        self.pred_y = 0
        self.goal_x = 0
        self.goal_y = 0

        self.reading = {
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

    def tick(self):
        read = self._uart.read(1)

        if read == b'11111111':
            self.counter = 0
            self.curr_float = []
        
        self.curr_float.append(read)

        if len(self.curr_float) == 4:
            # ready to parse a float
            curr_float = _parse_float(self.curr_float)
            if self.counter == 0:
                self.curr_x = curr_float
            elif self.counter == 1:
                self.curr_y = curr_float
            elif self.counter == 2:
                self.pred_x = curr_float
            elif self.counter == 3:
                self.pred_y = curr_float
            elif self.counter == 4:
                self.goal_x = curr_float
            elif self.counter == 5:
                self.goal_y = curr_float
                self.ready = True
                self._update_reading()
            
            self.counter += 1
            self.curr_float = []

    def _update_reading(self):
        self.reading = {
            "curr_x": self.curr_x,
            "curr_y": self.curr_y,
            "pred_x": self.pred_x,
            "pred_y": self.pred_y,
            "goal_x": self.goal_x,
            "goal_y": self.goal_x,
        }
    
    def get_reading(self):
        if self.ready:
            return self.reading
    
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
