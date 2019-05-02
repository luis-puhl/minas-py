from functools import wraps
import errno
import os
import signal
import platform

import time
import threading

class Alarm(threading.Thread):
  def __init__ (self, timeout):
    threading.Thread.__init__(self)
    self.timeout = timeout
    self.setDaemon(True)
  def run (self):
    time.sleep(self.timeout)
    print('Alarm Timeout')
    os._exit(1)

class TimeoutError(Exception):
  pass

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
  def decorator(func):
    def _handle_timeout(signum, frame):
      raise TimeoutError(error_message)

    def wrapper(*args, **kwargs):
      if platform.system() == 'Windows':
        alarm = Alarm(seconds)
        alarm.start()
        try:
          result = func(*args, **kwargs)
        finally:
          del alarm
        return result
      else:
        signal.signal(signal.SIGALRM, _handle_timeout)
        signal.alarm(seconds)
        try:
          result = func(*args, **kwargs)
        finally:
          signal.alarm(0)
        return result

    return wraps(func)(wrapper)

  return decorator