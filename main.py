# coding=UTF-8

alive = True

while alive:
    command = raw_input("").split(" ")
    if command[0] == "exit":
        alive = False
    else:
        print "No such command: %s" % command[0]
