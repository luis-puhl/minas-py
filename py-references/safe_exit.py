import time, os, signal
print(os.getpid())
def exit_gracefully(signum, frame):
    print('killed', signum)
    exit()
signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)
signal.signal(signal.SIGKILL, exit_gracefully)
signal.signal(signal.SIGQUIT, exit_gracefully)

try:
    while True:
        time.sleep(1)
        print('.')
        j = 0
        for i in range(10**5):
            j += i
except KeyboardInterrupt as ex:
    print('KeyboardInterrupt')
    print(repr(ex))
except BaseException as ex:
    print(repr(ex))
