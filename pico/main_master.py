import bt

if __name__ == "__main__":
    bt_module = bt.BluetoothCommunication(
        uart=0,
        tx=0,
        rx=0,
        key=0,
        master=True,
        slave_addr=""   #Add this in
    )

    done = False
    while done:
        bt_module.tick()

        if bt_module.ready:
            print(bt_module.get_reading())
            done = True