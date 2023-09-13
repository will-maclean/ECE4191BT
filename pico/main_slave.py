import bt

if __name__ == "__main__":
    bt_module = bt.BluetoothCommunication(
        uart=0,
        tx=0,
        rx=0,
        key=0,
        master=False,
    )

    state = {
            "curr_x": 1.1,
            "curr_y": 2.2,
            "pred_x": 3.3,
            "pred_y": 4.4,
            "goal_x": 5.5,
            "goal_y": 6.6,
        }

    bt_module.transmit_state(state)