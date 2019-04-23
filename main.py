
class Model:
  k = 100
  clusters = []
  radiusFactor = 1.1
  noveltyThr = 100
  lastExapleTMS = 0
  # -------- actions Thresholds ------------
  #ExND
  ndProcedureThr = 2000
  def ndProcedureThrFn(self):
    return self.representationThr * self.k
  #ExClu
  representationThr = 3
  def representationThrFn(self):
    return len self.unknownBuffer / self.k
  # Window size to forget outdated data
  forgetThr = 1000
  def forgetThrFn(self):
    return 2 * self.ndProcedureThr


class Cluster:
  center = []
  radius = 0
  label = ''
  counter = 0
  # statistic summary
  n = 0
  mean = []
  stdDev = 0
  max = []
  min = []