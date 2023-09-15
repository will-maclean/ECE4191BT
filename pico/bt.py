from machine import UART, Pin
import time
import ustruct

def parse_float(n):
    return ustruct.unpack('f', n)[0]

def encode_float(n: float):
    return ustruct.pack('f', n)

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

    def __init__(self, uart, tx, rx, state=None, baudrate=38400, slave_addr=None, master=True, passwd='1234') -> None:
        self._uart = UART(uart, baudrate=baudrate, tx=Pin(tx), rx=Pin(rx))
        self._state = Pin(state, Pin.IN) if state is not None else None

        self._master = master
        self._passwd = passwd
        self._slave_addr = slave_addr

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
    
    def configure_chip(self):
        print("Ensure EN pin is set high (3V3). Should be 1s on, 1s off flash")

        # just say hi
        print("Saying hello...")
        print(self._wr("AT\r\n"))

        # set the password
        self._wr(f"AT+PSWD={self._passwd}\r\n")

        if self._master:
            # master
            
            # clear any paired devices
            print("clearing paired devices")
            self._wr("AT+RMAAD\r\n")

            # set as master
            print("setting as master")
            self._wr("AT+ROLE=1\r\n")

            # set to manual pairing
            print("setting manual pairing")
            self._wr("AT+CMODE=0\r\n")

            # bind
            print("binding...")
            print(self._wr(f"AT+BIND={self._slave_addr}\r\n", sleep=10))

            print("If you got here - awesome. Remove EN from both chips and you should be in business")

        else:
            # slave

            # clear any paired devices
            self._wr("AT+RMAAD\r\n")

            # getting address
            self._wr("AT+ADDR?\r\n", sleep=2)
    
    def _wr(self, message, sleep=1):
        self._uart.write(message)
        time.sleep(sleep)
        return self._uart.read()

    def tick_read(self):
        if self._uart.any() >= 4:
            read = self._uart.read(4)

            print(read)
            curr_float = parse_float(read)
            print(curr_float)

            if curr_float == 4.191:
                self._counter = 0
                self._curr_float = []
                self._started = True

            if not self._started:
                return

            if self._counter == 1:
                self._curr_x = curr_float
            elif self._counter == 2:
                self._curr_y = curr_float
            elif self._counter == 3:
                self._pred_x = curr_float
            elif self._counter == 4:
                self._pred_y = curr_float
            elif self._counter == 5:
                self._goal_x = curr_float
            elif self._counter == 6:
                self._goal_y = curr_float
                self._ready = True
                self._started = False
                self._update_reading()
            
            self._counter += 1
            
    def _update_reading(self):
        self._reading = {
            "curr_x": self._curr_x,
            "curr_y": self._curr_y,
            "pred_x": self._pred_x,
            "pred_y": self._pred_y,
            "goal_x": self._goal_x,
            "goal_y": self._goal_y,
        }
    
    def get_reading(self):
        if self._ready:
            return self._reading
    
    def transmit_state(self, reading):
        # header
        self._uart.write(encode_float(4.191))

        # data
        self._uart.write(encode_float(reading['curr_x']))
        self._uart.write(encode_float(reading['curr_y']))
        self._uart.write(encode_float(reading['pred_x']))
        self._uart.write(encode_float(reading['pred_y']))
        self._uart.write(encode_float(reading['goal_x']))
        self._uart.write(encode_float(reading['goal_y']))
    
    def is_ready(self):
        return self._ready
    
    def factory_reset(self):
        return self._wr("AT+ORGL\r\n", sleep=10)
    
    def connected(self):
        if self._state is not None:
            return self._state.value()
