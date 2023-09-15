# Testing script for two BT modules connected to a single Pico.
# working!

import ECE4191BT.pico.bt as bt

if __name__ == "__main__":
    bt_master = bt.BluetoothCommunication(uart=0, tx=16, rx=17, state=18, baudrate=38400, master=True)
    bt_slave = bt.BluetoothCommunication(uart=1, tx=8, rx=9, state=13, baudrate=38400, master=False)

    # bt_master.factory_reset()
    # bt_slave.factory_reset()

    configure = False

    if configure:
        print("configuring slave")
        bt_slave.configure_chip()

        print("configuring master")
        bt_master.configure_chip()
    else:
        print("Starting transmission")
        state = {
            "curr_x": 1.1,
            "curr_y": 2.2,
            "pred_x": 3.3,
            "pred_y": 4.4,
            "goal_x": 5.5,
            "goal_y": 6.6,
        }

        bt_master.transmit_state(state)

        print("Reading transmission")
        done = False
        while not done:
            bt_slave.tick_read()

            if bt_slave.is_ready():
                print(bt_slave.get_reading())
                done = True