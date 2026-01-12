from badusb.command import Command

# Loads and executes commands from the payload
if __name__ == "__main__":
    payload = open("payload.txt", "r").read()
    Command().run(payload)
