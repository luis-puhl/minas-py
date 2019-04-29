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

![overview-2015.png](./ref/overview-2015.png)

---

### Overview (ii)

![overview_ND_procedure.jpg](./ref/overview_ND_procedure.jpg)

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

### Online Phase (iii)

![alg-online-2015.png](./ref/alg-online-2015.png)

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

# Intepretação (i)

> A new micro-cluster is representative if it contains a minimal number of examples
> A new micro-cluster is cohesive if its silhouette coefficient is larger than 0 (see Eq. 1). [...] $Silhouette = \frac{b − a}{max(b, a)}$ 
> [...] In Eq. 1, _b_ represents the Euclidean distance between the centroid of the new micro-cluster and the centroid of its closest micro-cluster, and _a_ represents the standard deviation of the distances between the examples of the new micro-cluster and the centroid of the new micro-cluster.

Portanto $b = closestClusterDist(C_i)$ e $a = C_r$

---


# Intepretação (ii)

Given an model $M$, an example $\vec{p}$; Clusters $C_1$ and $C_2$. Composed as 
$M = \begin{cases}
  C:& \text{cluster set}\\
  f^t:& \text{radius factor}\\
  N^t:& \text{representation Thr.}\\
  T^t:& \text{Novelty Threshold}\\
\end{cases}
$ and $C_i = \begin{cases}
  \vec{c}:& \text{center}\\
  r:& \text{radius, } \sigma\big(d(\vec{c}, \vec{x_i}) \big)\\
  l:& \text{label}\\
  n:& \text{counter}\\
\end{cases}
$

$$\begin{aligned}
\text{Classify: }& \vec{p} \in C_1 \iff d(C_{1.\vec{c}}, \space \vec{p}) \lt f^t \sdot C_{1 .r} ;\\

\text{Validity: } & C_1 \text{ is valid } \iff
 \underbrace{
  C_{1.n} \gt N^t
}_{\text{ is representative }}
\land
 \underbrace{
  \nexists C_2 / d(C_{1.\vec{c}}, \space C_{2.\vec{c}}) \le C_1{ .r}
}_{\text{ is cohesive }}
  ;\\

\text{Extention: }& C_{1.l} = C_{2.l} \iff d(C_{1.\vec{c}}, \space C_{2.\vec{c}}) \le T^t ;\\

\text{Novelty: }&  C_{1.l} \text{ is new label} \iff \nexists C_2 / d(C_{1.\vec{c}}, \space C_{2.\vec{c}}) \gt T^t .\\
\end{aligned}$$

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

---

# Porpostas de Implementação

## Algoritmo mínimo
  - Entradas constantes em source-code
  - Próximo do pseudo-code

---

## Usar poligonos (retângulos) _versus_ esferas
Atualmente representa um _micro-cluster_ ($M$) pela esfera $(\overrightarrow{centroid}, radius)$ onde _radius = standard deviation of the distance between the examples and the centroid_. Um exemplo $\vec{x} \in M \iff dist(\vec{x}, M_{centroid}) < f*M_{raidus}$

Poderia representar um _micro-cluster_ ($M$) pelo retângulo $M = (\vec{c}, \vec{r})$ onde $\vec{c}_i$ é a média e $\vec{r}_i$ é o desvio padrão para o componente $i$ dos exeplos desse _micro-cluster_. Então a pertinência de um exemlo não rotulado à um _micro-cluser_ seria:
$\large\vec{x} \in M \iff \lVert(\vec{x}_i - M_{\vec{c}_i})\rVert < \lVert f*M_{\vec{r}_i} \rVert$

Pode-se deduzir que esse processo pode ser mais preciso em data sets onde exitam, por exemplo, classes retangulares prómixas e paralelas em um dos atributos onde uma esfera cobriria ambas classes.

Além disso, como esses valores já são calculados indiretamente, somente o custo de armazenamento iria aumentar (pouquissimo)

---

## Paralelismo (i)

<!-- Modelo $M$ contém $k$ clusters, cada cluster é formado por $(\vec{c}, r)$ e, para que um exemplo $\vec{x}$ perteça ao cluster -->

$$\large \lfloor_{0 \le i\le k} \sum_{0 \le j \le n} (M_{i, c_{j}} - x_{j})^2 \rfloor < M_{i, r}$$

Pode-se distribuir na função mínimo, distribuindo clusters, ou na fução soma, distribuindo atributos.

---

- Usar data-set KYOTO
- Offilne serial