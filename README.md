# ECE4191BT

Communication library for ECE4191. Desired ports are:

- Raspberry Pi (not started)
- Raspberry Pi Pico (working)
- PSoC (not started)

Please feel free to contribute for your own hardware. Discussion around transmission protocol is here: https://docs.google.com/document/d/1ZaPLZT26EebmlPLHcU29AvFIRHO5OxfgUufaZEdOcd8/edit?usp=sharing

## Pico
Process for setup on Pi Pico

1. Connect EN pin to logic high (3V3) before powering chip on (this will start the chips in configuration mode)
2. If setting up a slave chip:
    1. Create a BT object: `bt_slave = bt.BluetoothCommunication(uart=X, tx=X, rx=X, state=X, baudrate=38400, master=False)`
    2. Run the configure command: `bt_slave.configure_chip()`
    3. Record the address that gets returned
3. If setting up a master chip:
    1. Create a BT object: `bt_master = bt.BluetoothCommunication(uart=X, tx=X, rx=X, state=X, baudrate=38400, master=True, slave_addr="XXXX,XX,XXXX")`
    2. Run the configure command: `bt_master.configure_chip()`
4. Hopefully there were no errors! If there are, reset either chip to factory defaults with `factory_reset()`
5. Remove the VCC pins and remove the EN pins
6. Plug the VCC pins in (this will restart the chips in communication mode)
7. Recreate the objects in software using the same constructors as above

Example transmit command is:

```python
state = {
    "curr_x": 1.1,
    "curr_y": 2.2,
    "pred_x": 3.3,
    "pred_y": 4.4,
    "goal_x": 5.5,
    "goal_y": 6.6,
}

bt_master.transmit_state(state)
```

Example read command:

```python
done = False
while not done:
    bt_slave.tick_read()

    if bt_slave.is_ready():
        print(bt_slave.get_reading())
        done = True
```