from networking import *
import time


def ping(_server):
    while True:
        _server.check_client_connection()
        time.sleep(1)


def command():
    while True:
        _command = raw_input("").split(" ")
        if _command[0] == "exit":
            server.close()
            exit()
        else:
            print "invalid command"
try:
    server = ServerSocket("", 12346)
    server.bind()
    server.setDaemon(True)
    server.start()

except Exception as err:
    print "Cannot create server on port " + str(server.port)
    print err
    exit()


thread.start_new_thread(ping, (server, ))
thread.start_new_thread(command, ())

while server.status != NET_SOCKET_CLOSED:
    try:
        if message_available(server):
            message = get_message(server)

            if message.read("flag") == NET_CONNECTION_ESTABLISHED:
                print "player %i connected" % message.read("sender")

            if message.read("flag") == NET_CONNECTION_CLOSED:
                print "player %i disconnected" % message.read("sender")

            if message.read("flag") == NET_CONNECTION_PING:
                print "player %i pong" % message.read("sender")

    except KeyboardInterrupt:
        print "closing server..."
        server.close()
        exit()
