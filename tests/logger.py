import inspect, sys, os

class Logger(object):
  __slots__ = ['fileName', 'terminal', 'log', 'silent', 'line']
  def __init__(self, fileName, silent=False):
    self.terminal = sys.stdout
    self.fileName = fileName
    self.silent = silent
    self.line = ''
  def __enter__(self):
    dirr = os.path.dirname(self.fileName)
    if not os.path.exists(dirr):
      os.makedirs(dirr)
    self.log = open(self.fileName, 'a')
    sys.stdout = self
    return self
  def __exit__(self, exc_type, exc_value, traceback):
    sys.stdout = self.terminal
    self.log.close()
    return self
  def write(self, message):
    if self.silent:
      return len(message)
    self.line = self.line + message
    if '\n' in message:
      self.writeLine()
    return len(message)
  def writeLine(self):
    try:
      stack = inspect.stack()
      if len(stack) > 2:
        self.line = str(stack[1].filename) + ':' + str(stack[1].lineno) + ' ' + self.line
    except Exception as ex:
      self.terminal.write(str(ex))
    self.terminal.write(self.line)
    self.log.write(self.line)
    self.line = ''
  def flush(self):
    self.log.flush()

if __name__ == "__main__":
  print('Test Logger')
  import shutil
  if os.path.exists('test_logger'):
    shutil.rmtree('test_logger')
  with Logger('test_logger/test.log'):
    print('echo')
    print('echo', 'and', 'more args')
  # if os.path.exists('test_logger'):
  #   shutil.rmtree('test_logger')
  print('End Test Logger')
  