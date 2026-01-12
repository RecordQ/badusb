from glob import glob
from badusb.command import Command

# Loads and executes commands from the payload
if __name__ == "__main__":
    for file in glob("payloads/*.dd"):
        payload = open(file, "r").read()
        Command().run(payload)
