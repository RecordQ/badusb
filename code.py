from badusb.command import Command

# Loads and executes commands from the payload
if __name__ == "__main__":
    command = Command()
    command.execute("payloads/payload.dd")
