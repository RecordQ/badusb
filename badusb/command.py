from time import sleep, time
from board import LED, GP5
from digitalio import DigitalInOut, Direction, Pull
import random
from .keyboard import Keyboard
from .mouse import Mouse


# Command handler class
class Command:
    # Initial setup
    def __init__(self) -> None:
        self.__keyboard = Keyboard()
        self.__mouse = Mouse()
        self.__led = DigitalInOut(LED)
        self.__led.direction = Direction.OUTPUT
        self.__typespeed = 0.0
        self.__delay = 0.5

        # Execution state
        self.lines = []
        self.line_index = 0
        self.repeat_stack = []
        self.functions = {}
        self.call_stack = []

        self.__string = ""
        self.__arguments = []
        self.__pause()

    # Pauses the load execution
    def __pause(self) -> None:
        gp5 = DigitalInOut(GP5)
        gp5.switch_to_input(pull=Pull.UP)

        while not gp5.value:
            pass

    # Alias to HOTKEY
    def press(self) -> None:
        self.hotkey()

    # Enters a key combination
    def hotkey(self) -> None:
        keycodes = []

        for argument in self.__arguments:
            if len(argument) == 1:
                ordinal = ord(argument.lower())

                if ordinal < 0x80:
                    keycode = self.__keyboard.ASCII[ordinal]

                    keycodes.append(*keycode)

            elif hasattr(Keyboard, argument.upper()):
                keycodes.append(getattr(Keyboard, argument.upper()))

        self.__keyboard.hotkey(*keycodes)

    # Enters a string of ASCII characters
    def string(self) -> None:
        self.__keyboard.string(self.__string, self.__typespeed)

    # Sets the type speed of strings
    def typespeed(self) -> None:
        if len(self.__arguments) > 0:
            self.__typespeed = int(self.__arguments[0]) / 1000

    # Sets the delay between commands
    def delay(self) -> None:
        if len(self.__arguments) > 0:
            time = int(self.__arguments[0]) / 1000

        else:
            time = self.__delay

        sleep(time)

    # Turns on/off the onboard LED diode
    def led(self) -> None:
        if len(self.__arguments) > 0:
            if self.__arguments[0].lower() == "on":
                self.__led.value = True

            else:
                self.__led.value = False

    # Types a mixed number based on input 0-9
    def say(self) -> None:
        if len(self.__arguments) > 0:
            arg = self.__arguments[0]
            if len(arg) == 1 and arg.isdigit():
                digit = int(arg)
                # Mapping: 0->9, 1->5, 2->8, 3->0, 4->2, 5->7, 6->1, 7->3, 8->6, 9->4
                mapping = {
                    0: "9",
                    1: "5",
                    2: "8",
                    3: "0",
                    4: "2",
                    5: "7",
                    6: "1",
                    7: "3",
                    8: "6",
                    9: "4",
                }
                mapped_char = mapping.get(digit)
                if mapped_char:
                    self.__keyboard.string(mapped_char, self.__typespeed)

    # Executes instructions and validates them
    def execute(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as payload:
            self.run(payload.read())

    # Executes instructions and validates them
    def run(self, text: str) -> None:
        self.lines = text.splitlines()
        self.line_index = 0

        # Reset state
        self.repeat_stack = []
        self.call_stack = []
        self.functions = {}

        # First pass: find functions
        for i, line in enumerate(self.lines):
            parts = line.strip().split(" ")
            if len(parts) > 0 and parts[0].upper() == "FUNCTION" and len(parts) > 1:
                self.functions[parts[1]] = i

        while self.line_index < len(self.lines):
            line = self.lines[self.line_index].strip()
            self.__string = line.replace("\n", "").replace("\r", "")
            self.__arguments = self.__string.split(" ")

            if len(self.__arguments) > 0 and self.__arguments[0]:
                command = self.__arguments.pop(0).lower()

                if hasattr(self, command):
                    # Strip command from string for the string() method
                    # This matches the original logic: self.__string = self.__string[len(command) + 1 :]
                    # But we need to be careful about spaces.
                    # If we split by space, we can just rejoin or substring.
                    # Simple substring approach:
                    if len(self.__string) > len(command) + 1:
                        self.__string = self.__string[len(command) + 1 :]
                    else:
                        self.__string = ""

                    try:
                        getattr(self, command)()
                    except Exception as e:
                        self.__keyboard.release()

            self.line_index += 1

    def mouse(self) -> None:
        if len(self.__arguments) > 0:
            cmd = self.__arguments.pop(0).upper()
            if cmd == "MOVE" and len(self.__arguments) >= 2:
                self.__mouse.move(int(self.__arguments[0]), int(self.__arguments[1]))
            elif cmd == "CLICK" and len(self.__arguments) >= 1:
                btn = self.__arguments[0].upper()
                mask = 0
                if "LEFT" in btn:
                    mask |= 1
                if "RIGHT" in btn:
                    mask |= 2
                if "MIDDLE" in btn:
                    mask |= 4
                self.__mouse.click(mask)
            elif cmd == "SCROLL" and len(self.__arguments) >= 1:
                self.__mouse.move(wheel=int(self.__arguments[0]))

    def repeat(self) -> None:
        if len(self.__arguments) > 0:
            count = int(self.__arguments[0])
            self.repeat_stack.append([self.line_index, count])

    def end_repeat(self) -> None:
        if self.repeat_stack:
            start_index, count = self.repeat_stack[-1]
            if count > 1:
                self.repeat_stack[-1][1] -= 1
                self.line_index = start_index
            else:
                self.repeat_stack.pop()

    def function(self) -> None:
        while self.line_index < len(self.lines):
            parts = self.lines[self.line_index].strip().split(" ")
            if len(parts) > 0 and parts[0].upper() == "END_FUNCTION":
                break
            self.line_index += 1

    def end_function(self) -> None:
        if self.call_stack:
            self.line_index = self.call_stack.pop()

    def call(self) -> None:
        if len(self.__arguments) > 0:
            name = self.__arguments[0]
            if name in self.functions:
                self.call_stack.append(self.line_index)
                self.line_index = self.functions[name]

    def random_delay(self) -> None:
        if len(self.__arguments) >= 2:
            min_ms = int(self.__arguments[0])
            max_ms = int(self.__arguments[1])
            sleep(random.randint(min_ms, max_ms) / 1000)

    def _get_pin(self, pin_name: str):
        # Helper to get pin object safely
        import board

        pin_name = pin_name.upper()
        if hasattr(board, pin_name):
            return getattr(board, pin_name)
        return None

    def wait_for_button(self) -> None:
        if len(self.__arguments) > 0:
            pin_name = self.__arguments[0].upper()
            pin_obj = self._get_pin(pin_name)
            if pin_obj:
                button = DigitalInOut(pin_obj)
                button.switch_to_input(pull=Pull.UP)
                # Wait for press (LOW because pull UP)
                while button.value:
                    sleep(0.01)
                button.deinit()

    def if_button(self) -> None:
        if len(self.__arguments) > 0:
            pin_name = self.__arguments[0].upper()
            pin_obj = self._get_pin(pin_name)
            pressed = False
            if pin_obj:
                button = DigitalInOut(pin_obj)
                button.switch_to_input(pull=Pull.UP)
                pressed = not button.value
                button.deinit()

            if not pressed:
                # Scan for END_IF
                nesting = 0
                while self.line_index < len(self.lines):
                    self.line_index += 1
                    if self.line_index >= len(self.lines):
                        break

                    line_parts = self.lines[self.line_index].strip().split(" ")
                    if not line_parts:
                        continue

                    cmd = line_parts[0].upper()
                    if cmd == "IF_BUTTON":
                        nesting += 1
                    elif cmd == "END_IF":
                        if nesting == 0:
                            break
                        nesting -= 1

    def end_if(self) -> None:
        pass
