from machine import UART, Pin
import time

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

    def __init__(self, uart, tx, rx, baudrate=38400, master=True, passwd='1234') -> None:
        self._uart = UART(uart, baudrate=baudrate, tx=Pin(tx), rx=Pin(rx))

        self._master = master
        self._passwd = passwd

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
            self._wr(f"AT+RMAAD\r\n")

            # set as master
            print("setting as master")
            self._wr(f"AT+ROLE=1\r\n")

            # reset
            print("resetting")
            self._wr(f"AT+RESET\r\n")

            # set to manual pairing
            print("setting manual pairing")
            self._wr(f"AT+CMODE=0\r\n")

            # setup inquiry mode
            print("configuring inquiry mode")
            self._wr(f"AT+INQM=0,5,9\r\n")

            # setup SSP mode
            print("configuring SSP")
            print(self._wr(f"AT+INIT\r\n"))

            # inquire for BT devices
            print("searching for devices")
            print(self._wr(f"AT+INQ\r\n", sleep=10))

            # query for host names and check which address we want
            resp = None
            addr = None
            while resp != 'done':
                print("Note -> replace colons with commas")
                resp = input("enter an address to query hostname, or 'done' if last address was correct, or 'rescan': ")

                if resp == 'done':
                    break
                elif resp == 'rescan':
                    print("searching for devices")
                    print(self._wr(f"AT+INQ\r\n", sleep=10))
                else:
                    print(self._wr(f"AT+RNAME?{resp}\r\n"))
                    addr = resp
            
            # pair with the device
            print("pairing...")
            print(self._wr(f"AT+PAIR={addr},9\r\n", sleep=10))

            # bind
            print("binding...")
            print(self._wr(f"AT+BIND={addr}\r\n", sleep=10))

            # set master to only connect with paired devices
            print(self._wr(f"AT+CMODE=1\r\n"))

            # link
            print("linking...")
            print(self._wr(f"AT+LINK={addr}\r\n", sleep=10))

            print("If you got here - awesome. Remove EN from both chips and you should be in business")

        else:
            # slave

            # clear any paired devices
            self._wr(f"AT+RMAAD\r\n")

            # set as slave
            self._wr(f"AT+ROLE=0\r\n")

            # reset
            self._wr(f"AT+RESET\r\n")

            # set to auto pairing
            self._wr(f"AT+CMODE=1\r\n")
    
    def _wr(self, message, sleep=1):
        self._uart.write(message)
        time.sleep(sleep)
        return self._uart.read()

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
    
    def factory_reset(self):
        return self._wr("AT+RESET\r\n")
