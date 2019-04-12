---
marp: true
---

# Algoritmo Paralelo para Detecção de novidades em fluxo de dados

MINAS: multiclass learning algorithm for novelty detection in data streams

---

## Novelty Detection Algorithm for Data Streams Multi-Class Problems (2013)

### Elaine R. Faria, João Gama, André C. P. L. F. Carvalho

Keywords: Novelty detection, multi-class, data stream, clustering

---

### Overview (i)

![overview-online-2013.png](./ref/overview-online-2013.png)

---

```
Algorithm 1 MINAS: Offline Phase
Require: kini, algorithm, TrainingSet
for all classes Ci in TrainingSet do
  ModelTmp ← Clustering(TrainingSetClass=Ci , kini, algorithm)
  for all hyperspheres h in ModelTmp do
    Labelh ← Ci
  end for
  Model ← Model ∪ ModelTmp
end for
return Model
```

_Clustering_ returns hypersphere of type `{center, radius, label}`.

---

```
Algorithm 2 MINAS: Online Phase
Require: T, Model, Stream, NumMinExamples
ShortTimeMem ← ∅
for all elem in Stream do
  if elem is inside an hypersphere h of Model then
    Classify elem in Class Labelh
  else
    Classify elem as Unk
    ShortTimeMem ← ShortTimeMem ∪ elem
    if |ShortTimeMem| ≥ NumMinExamples then
      Model ← Novelty-Extension-Detection (Model, T, ShortTimeMem)
    end if
  end if
end for
```

---

`Require: Model, T = threshold, ShortTimeMem` was omited.

```
Algorithm 3 Novelty-Extension-Detection
ModelTemp ← k-Means(ShortTimeMem, k)
for all hypersphere h1 in ModelTemp do
  if Validation-Criterion(h1) then
    Let h the nearest hypersphere to h1 (h ∈ Model)
    Let d the distance between h1 and h
    if d ≤ T then
      Labelh1 ← Labelh {Extension}
    else
      Labelh1 ← new label {New concept}
    end if
    Model ← Model ∪ h1
  else
    k = update()
  end if
end for
return Model
```

---

## Validation-Criterion function

> A new cluster is considered valid if its cohesiveness, defined by the sum of squared distances between examples and centroid divided by the number of examples, is at least half of the cohesiveness of the normal model. If a new cluster is valid, it is necessary to decide if it represents

It really means _1-mean_ (k-mean where k=1) of _short-time memory_ to extract the
`radius` component from the returning cluster.

$$cohesiveness(x, c) = \cfrac{ \sum d(x_i, c)^2} {|x|} = \cfrac{ \sum _{0<i<|x|} (x_i - c) \cdot (x_i - c)} {|x|}$$

Where $x$ is `hypersphere.examples` and $c$ is `hypersphere.center`.

So the Novelty-Extension-Detection would look like:

```
for all hypersphere h1 in ModelTemp do
  if h1.cohesiveness >= (Model.cohesiveness /2) then
```

---

## $k$ update function

> The value of k is adjusted whenever a cluster is considered invalid, according to the following conditions [14]: 
> i) If most of clusters are invalid because they have low density, the value of k is increased;
> ii) If most of clusters are invalid because they have few ex-because they have low density, the value of k is increased;
> iii) If all clusters are valid, the k value is not adjusted.

## $T$ threshold euristics

The param $T$ controls the _evolutin or novelty_ decision for a new class. In the study is proportional to cluster cohesion by a factor $f$ fo $1.1$.

---

## Conclusion

> MINAS presented better results than OLINDDA for ~~five~~ 4 UCI data sets;
> [...]
> Using an artificial data set, MINAS was capable to differentiate two new concepts in the online phase and to correctly classify new examples;
> [...]
> The next steps include the investigation of non-spherical clustering techniques to better represent the classes,
> and the development new approaches for the automatic choice of the threshold value.

---

## MINAS: multiclass learning algorithm for novelty detection in data streams (2015)

### Elaine Ribeiro de Faria, André Carlos Ponce de Leon Ferreira Carvalho, João Gama

Keywords: Novelty detection, Data streams, Multiclass classification, Concept evolution

Received: 10 November 2014 / Accepted: 9 August 2015 / Published online: 22 August 2015

---

### Overview (i)

![overview_ND_procedure.jpg](overview_ND_procedure.j./ref/pg)

---

### Overview (ii) - Major Contributions

1) The use of **only one decision model (composed of different clusters)** representing the problem classes, learned in the training phase, or in the online phase;
2) The use of a **set of cohesive and unlabeled examples**, not explained by the current model, is used to learn new concepts or extensions of the known concepts, making the **decision model dynamic**;
3) Detection of different _novelty patterns_ and their learning by a decision model, representing therefore a multiclass scenario where the **number of classes is not fixed**;
4) Outliers, isolated examples, are not considered as a _novelty pattern_, because a _novelty pattern_ is composed of a cohesive and representative group of examples;
5) The decision model is updated **without external feedback**, or using a small set of labeled examples, even when available.

---

### Offline Phase

```
Require:
  k: number of micro-clusters,
  alg: clustering algorithm,
  S: Training Set

Model ← ∅
for all (class Ci in S) do
  ModelTmp ← Clustering(SClass=Ci ,k,alg)
  for all (micro-cluster micro in ModelTmp) do
    micro.label ← Ci ;
  end for
  Model ← Model ∪ ModelTmp;
end for
return Model
```

---

### Online Phase (i)

```
Require:
  Model: decision model from initial training phase,
  DS: data stream,
  T: threshold,
  NumExamples: minimal number of examples
    to execute a ND procedure,
  windowsize: size of a data window,
  alg: clustering algorithm

ShortMem ← ∅
SleepMem ← ∅
```

---

### Online Phase (ii)

```
for all (example ex in DS) do
  (Dist, micro) ← closer-micro(ex,Model)
  if (Dist ≤ radius(micro) then
    ex.class ← micro.label
    update-micro(micro,ex)
  else
    ex.class ← unknown
    ShortMem ← ShortMem ∪ ex
    if (|ShortMem| ≥ NumExamples) then
      Model ← novelty-detection
        (Model, ShortMem, SleepMem, T, alg)
    end if
  end if
  CurrentTime ← ex.time
  if (CurrentTime mod windowSize == 0) then
    Model ← move-sleepMem
      (Model, SleepMem, CurrentTime, windowSize)
    ShortMem ← remove-oldExamples
      (ShortMem, windowsize)
  end if
end for
```

---

### Novelty Detection (i)

```
Require:
  Model: current decision model,
  ShortMem: short-term memory,
  SleepMem: sleep memory,
  T: threshold,
  alg: clustering algorithm
```

---

### Novelty Detection (ii)

```
ModelTmp ← Clustering(ShortMem, k, alg)
for all (micro-grupo micro in ModelTemp) do
  if ValidationCriterion(micro) then
    (Dist, microM) ← closest-micro(micro,Model)
    if Dist ≤ T then
      micro.label ← microM.label
    else
      (Dist, microS) ← closest-micro(micro,SleepMem)
      if Dist ≤ T then
        micro.label ← microS.label
      else
        micro.label ← new label
      end if
    end if
    Model ← Model ∪ micro
  end if
end for
return Model
```

---

## Novelty detection in data streams (2015)

### Elaine R. Faria, Isabel J. C. R. Gonçalves, André C. P. L. F. de Carvalho, João Gama

Keywords: Novelty detection, Data streams, Survey, Classification

Published online: 27 Octorber 2015

---

## Cassales, Guilherme Weigert (2018)

```
Entrada: Modelo, FCD, T, NumMinExemplos, ts, P
MemTmp ← ∅
MemSleep ← ∅
for all exemplo in FCD do
  (Dist,micro) ← micro-mais-proximo(exemplo,Modelo)
  if Dist < raio(micro) then
    exemplo.classe ← micro.rotulo
    atualizar-micro(micro,exemplo)
  else
    exemplo.classe ← desconhecido
    MemTmp ← MemTmp ∪ exemplo
    if |MemTmp| ≥ NumMinExemplos then
      Modelo ← deteccao-novidade(Modelo,MemTmp,T)
    end if
  end if
  TempoAtual ← exemplo.T
  if TempoAtual mod TamJanela == 0 then
    Modelo ← mover-micro-grupos-mem-sleep
      (Modelo,MemSleep,P)
    MemTmp ← remover-exemplos-antigos(MemTmp,ts)
  end if
end for
```
