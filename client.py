from networking import *

try:
    client = ClientSocket("127.0.0.1", 12346)
    client.connect()

except Exception as err:
    print err
    exit()

while client.status != NET_SOCKET_CLOSED:
    try:
        if message_available(client):
            message = get_message(client)

            if message.read("flag") == NET_CONNECTION_ESTABLISHED:
                print "connected to server"

            if message.read("flag") == NET_CONNECTION_CLOSED:
                print "disconnected from server"
                break

            if message.read("flag") == NET_CONNECTION_PING:
                print "ping"
                client.ping(client.socket)
    except KeyboardInterrupt:
        client.close()
        exit()
