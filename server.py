from networking import *

server = ServerSocket("", 12345)
server.bind()
server.setDaemon(True)
server.start()

while True:
    if message_available(server):
        message = get_message(server)

        if message.read("flag") == NET_CONNECTION_ESTABLISHED:
            print "player %i connected" % message.read("sender")

        if message.read("flag") == NET_CONNECTION_CLOSED:
            print "player %i disconnected" % message.read("sender")