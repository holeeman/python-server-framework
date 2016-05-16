from threading import Thread
import time

flag = True


def get_input():
    while flag:
        i = raw_input("")
        if i == "exit":
            global flag
            flag = False
        else:
            print i
inputs = Thread(target=get_input)
inputs.start()
while flag:
    print "waiting..."
    time.sleep(1)