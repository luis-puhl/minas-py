
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

class Minas():
  def offline(self, k, training_set):
    # Require:
    #   k: number of micro-clusters,
    #   alg: clustering algorithm,
    #   S: Training Set
    #
    # Model ← ∅
    # for all (class Ci in S) do
    #   ModelTmp ← Clustering(SClass=Ci ,k,alg)
    #   for all (micro-cluster micro in ModelTmp) do
    #     micro.label ← Ci ;
    #   end for
    #   Model ← Model ∪ ModelTmp;
    # end for
    # return Model
    pass
  
  def online(self, k, training_set):
    # Require:
    #   Model: decision model from initial training phase,
    #   DS: data stream,
    #   T: threshold,
    #   NumExamples: minimal number of examples to execute a ND procedure,
    #   windowsize: size of a data window,
    #   alg: clustering algorithm
    #
    # ShortMem ← ∅
    # SleepMem ← ∅
    #
    # for all (example ex in DS) do
    #   (Dist, micro) ← closer-micro(ex,Model)
    #   if (Dist ≤ radius(micro) then
    #     ex.class ← micro.label
    #     update-micro(micro,ex)
    #   else
    #     ex.class ← unknown
    #     ShortMem ← ShortMem ∪ ex
    #     if (|ShortMem| ≥ NumExamples) then
    #       Model ← novelty-detection(Model, ShortMem, SleepMem, T, alg)
    #     end if
    #   end if
    #   CurrentTime ← ex.time
    #   if (CurrentTime mod windowSize == 0) then
    #     Model ← move-sleepMem(Model, SleepMem, CurrentTime, windowSize)
    #     ShortMem ← remove-oldExamples(ShortMem, windowsize)
    #   end if
    # end for
    pass

  def noveltyDetection(self, parameter_list):
    # Require:
    #   Model: current decision model,
    #   ShortMem: short-term memory,
    #   SleepMem: sleep memory,
    #   T: threshold,
    #   alg: clustering algorithm
    # 
    # ModelTmp ← Clustering(ShortMem, k, alg)
    # for all (micro-grupo micro in ModelTemp) do
    #   if ValidationCriterion(micro) then
    #     (Dist, microM) ← closest-micro(micro,Model)
    #     if Dist ≤ T then
    #       micro.label ← microM.label
    #     else
    #       (Dist, microS) ← closest-micro(micro,SleepMem)
    #       if Dist ≤ T then
    #         micro.label ← microS.label
    #       else
    #         micro.label ← new label
    #       end if
    #     end if
    #     Model ← Model ∪ micro
    #   end if
    # end for
    # return Model
    pass

  def clustering(self, parameter_list):
    raise NotImplementedError
