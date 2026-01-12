from usb_hid import Device


class Mouse:
    def __init__(self):
        self._mouse = Device.MOUSE

    def move(self, x: int = 0, y: int = 0, wheel: int = 0):
        # Move the mouse. x, y, and wheel are strictly -127 to 127
        while x != 0 or y != 0 or wheel != 0:
            partial_x = max(-127, min(127, x))
            partial_y = max(-127, min(127, y))
            partial_wheel = max(-127, min(127, wheel))

            self._mouse.move(x=partial_x, y=partial_y, wheel=partial_wheel)

            x -= partial_x
            y -= partial_y
            wheel -= partial_wheel

    def click(self, buttons: int):
        self._mouse.click(buttons)

    def press(self, buttons: int):
        self._mouse.press(buttons)

    def release(self, buttons: int):
        self._mouse.release(buttons)

    def release_all(self):
        self._mouse.release_all()
