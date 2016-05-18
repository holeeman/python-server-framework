# coding=UTF-8
from networking import *
import struct

alive = True
server = ServerSocket("", 12345)

while alive:
    command = raw_input("").split(" ")
    if command[0] == "exit":
        alive = False
    else:
        print "No such command: %s" % command[0]
