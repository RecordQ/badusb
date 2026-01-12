import glob
from badusb.command import Command

# Loads and executes commands from the payload
if __name__ == "__main__":
    command = Command()
    for file in glob.glob("payloads/*.dd"):
        payload = open(file, "r").read()
        command.run(payload)
    command.execute("payloads/payload.dd")
