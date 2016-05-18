from networking import *

client = ClientSocket("127.0.0.1", 12345)
client.connect()
client.start()

while True:
    if message_available(client):
        message = get_message(client)

        if message.read("flag") == NET_CONNECTION_ESTABLISHED:
            print "connected to server"

        if message.read("flag") == NET_CONNECTION_CLOSED:
            print "disconnected from server"
            break
