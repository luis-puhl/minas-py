//MINAS - published in SAC 2013 - Track DS
package NoveltyDetection;

import java.util.*;
import java.io.*;
import moa.cluster.Clustering;
import weka.core.*;

//Class MINAS
public class MINAS {
    private String filenameOffline; // filename used in offline phase
    private String filenameOnline; // filename used in online phase
    private String outputDirectory; // name of the outuput directory

    private double threshold; // used to separate novelties from extensions
    private int minExCluster = 20; // minimum number of examples in a new valid cluster
    private String validationCriterion = "dec"; // validation criterion: dec --> mean distance
    private String algClusteringOff = "clustream";// clustering algorithm (offline phase): "kmeans" or "clustream"
    private String algClusteringOnl = "clustream";// clustering algorithm (online phase): "kmeans" or "clustream"
    private int numMicro = 100; // number of Micro clusters (used by clustream or kmeans algorithm)
    FileWriter fileOut; // file-Out with the results of the MINAS
    FileWriter fileOutClasses; // file-Out with the name of the classes of the problem
    ArrayList<Cluster> model; // decision model used to classify new examples (set of clusters)
    ArrayList<Cluster> SleepModeMem; // temporary memory where are stored the clusters that does not receive examples
                                     // for a long time
    int thresholdForgettingPast; // threshold used to put a cluster in the SleepMode
    private ArrayList<String[]> dataUnk; // memory containing the elements not explained by the current model (unknown)
    private int timestamp = -1; // current timestamp

    private String currentState; // current state of the process: offlien or online
    private int flagEvaluationType; // evaluation type: 0 -- proposed metodology, 1 -- methodology from the
                                    // literature
    private boolean flagMicroClusters;
    private int lastCheck = 0;

    /********************* Methods: Set **********************************************/
    public void setPar_minexcl(int minExClus) {
        this.minExCluster = minExClus;
    }

    // public void setPar_valcrit(String valcrit) {
    // this.validationCriterion = valcrit;
    // }
    public void setPar_nromicro(int par_nromicro) {
        this.numMicro = par_nromicro;
    }

    /********************* Constructor ***********************************************/
    public MINAS(String fileOff, String fileOnl, String outDirec, String algOff, String algOnl, double threshold,
            int evaluationType, int thresholdForgetPast, int nMicro, boolean flag) throws IOException {
        this.filenameOffline = fileOff;
        this.filenameOnline = fileOnl;
        this.algClusteringOff = algOff;
        this.algClusteringOnl = algOnl;
        this.outputDirectory = outDirec + "\\out_MINAS\\" + algOff + "\\" + algOnl + "_minexcl" + minExCluster
                + "_valcrit" + validationCriterion + "_algOff" + algOff + "_t" + threshold + "_f" + thresholdForgetPast;
        this.threshold = threshold;
        this.flagEvaluationType = evaluationType;
        this.thresholdForgettingPast = thresholdForgetPast;
        this.numMicro = nMicro;
        this.flagMicroClusters = flag;
        // createDirectory();
        File dir = new File(outputDirectory);
        if (dir.exists())
            dir.delete();
        else if (dir.mkdirs()) {
            System.out.println("Directory created successfully");
        }
    }

    /********************* validationcriterion ***************************************/
    public void validationcriterion() {
        if (validationCriterion.compareTo("dec") != 0) {
            // if (validationCriterion.compareTo("wss") != 0 &&
            // validationCriterion.compareTo("dec") != 0 &&
            // validationCriterion.compareTo("vol") != 0) {
            System.out.println("Invalid parameter(s).\n\n");
            System.exit(0);
        }
    }

    /********************* Offline ***************************************************/
    public ArrayList<String> offline() throws IOException {
        // creating one training file per class
        SeparateFiles sp = new SeparateFiles();
        ArrayList<String> classesOffline = sp.SeparateFileOff(filenameOffline);
        System.out.print("\n Classes for the training phase (offline): ");
        System.out.println("" + classesOffline.size());

        model = new ArrayList<Cluster>();
        ArrayList<Cluster> clusterSet = null;
        // each class is represented by a set of clusters
        for (String cl : classesOffline) {
            System.out.println("Class " + cl);
            int[] vectorResClustering = new int[1];
            // if the algorithm for clustering is Clustream
            if (algClusteringOff.equals("clustream")) {
                clusterSet = createModelClustream(filenameOffline, cl, vectorResClustering);
                // if the algorithm for clustering is kmeans
            } else if (algClusteringOff.equalsIgnoreCase("kmeans")) {
                clusterSet = createModelKMeans(filenameOffline + cl, numMicro, cl, null, vectorResClustering);
            }
            for (int i = 0; i < clusterSet.size(); i++)
                model.add(clusterSet.get(i));
        }
        // recording the number of classes of the training phase
        for (int g = 0; g < classesOffline.size(); g++) {
            fileOutClasses.write(classesOffline.get(g));
            fileOutClasses.write("\r\n");
        }
        fileOutClasses.close();
        return classesOffline;
    }

    /********************* stringResultClassification ********************************/
    public String stringResultClassification(String retorno[]) {
        String textoArq = "";

        if (retorno[1].equals("normal")) {
            textoArq = "C " + retorno[0];
        }
        // exemplo pertence a extensao de uma classe conhecida
        else if (retorno[1].equals("ext")) {
            textoArq = "ExtCon " + retorno[0];
        }
        // exemplo pertence a uma classe aprendida na fase online (novidade)
        if (retorno[1].equals("nov")) {
            textoArq = "N " + retorno[0];
        }
        // exemplo pertence a extensao de uma classe aprendida na fase online (novidade)
        if (retorno[1].equals("extNov")) {
            textoArq = "ExtNov " + retorno[0];
        }

        return textoArq;
    }

    /********************* classify ***************************************************/
    public int classify(Evaluation av, int count_k, String[] dataEx, String textFileOut, int countEx,
            ArrayList<Double> vectorMeasuresModelOffline, ArrayList<String> Novelties) throws IOException {
        int size = dataEx.length;
        double[] dataExDouble = new double[size - 1];
        for (int j = 0; j < size - 1; j++) {
            dataExDouble[j] = Double.valueOf(dataEx[j]);
        }

        // to verify if the example belongs to one of the existing clusters
        String[] vectorResult = identifyExample(dataExDouble);
        if (vectorResult != null) {
            // ********** example identify belonging to one of the clusters that composes
            // the currrent Model
            String strResClass = stringResultClassification(vectorResult);
            textFileOut = textFileOut + strResClass;

            // printing in the FileOut
            fileOut.write(textFileOut);
            fileOut.write("\n");
            av.addExampleConfusionMatrix(textFileOut);
        } else {
            // ********** Example identified as unknown******************************
            textFileOut = textFileOut + "Unk ";
            fileOut.write(textFileOut);
            fileOut.write("\n");
            av.addExampleConfusionMatrix(textFileOut);

            // Adding example to data unknown
            dataUnk.add(dataEx);

            // if the number of examples in dataUnk exceed a limit, the remove the oldest
            // one
            /*
             * if(dataUnk.size() > maxExUnk ) { dataUnk.remove(0); }
             */

            // ********** Searching for new clusters ****************************
            // if there are a sufficient number of examples to execute a clustering
            // procedure
            // and the last check had been executed at least (count_k*minExCluster) time
            // units earlier
            // Se o numero de exemplos eh suficiente (eh possivel gerar grupos com, em
            // media, o numero minimo de exemplos)
            count_k = numMicro;
            if ((dataUnk.size() >= count_k * minExCluster) && (lastCheck + (count_k * minExCluster) < countEx)) {
                lastCheck = countEx;

                // criando contadores, toosparse (estao muito longes), toofew (sao poucos)
                int temp_count_toosparse = 0;
                int temp_count_toofewex = 0;

                // set of elements to be removed from dataUnk if its cluster is valid
                int[] tmpRemove = new int[dataUnk.size()];
                // creating temporary model (set of clusters) from unknown data --> clustering
                // procedure
                ArrayList<Cluster> tmpModelUnk = createTmpModelUnk(count_k, tmpRemove);
                int flgTodosInvalidos = 1;

                // temporary confusion matrix
                Hashtable confusionMatrixTmp = new Hashtable();
                // verify if each cluster candidate (obtained from clustering process) is valid
                for (int cluster = 0; cluster < tmpModelUnk.size(); cluster++) {
                    Cluster clusterUnk = tmpModelUnk.get(cluster);
                    // if the cluster has the minimum number of examples
                    if (clusterUnk.getSize() >= minExCluster) {
                        // If the validation criterion is dec and
                        // the current cluster has the meanDistExCen <= maximum meanDistExCen from the
                        // offline model * 2
                        if (((validationCriterion.equalsIgnoreCase("dec"))
                                && (clusterUnk.getMeanDistance() <= max(vectorMeasuresModelOffline) * 2))) {
                            flgTodosInvalidos = 0;
                            // ********** The cluster is valid ****************
                            // creating confusion matrix relative to this cluster
                            confusionMatrixTmp = new Hashtable();
                            for (int elem = 0; elem < tmpRemove.length; elem++) {
                                // to set with -1 the examples to be removed from dataUnk
                                if (tmpRemove[elem] == cluster) { // if the cluster of the unknown example == to the
                                                                  // i_th valid cluster
                                    tmpRemove[elem] = -1; // then this example must be removed from the dataUnk

                                    // update temporary confusion matrix
                                    if ((confusionMatrixTmp.get("C " + dataUnk.get(elem)[size - 1])) == null) {
                                        confusionMatrixTmp.put("C " + dataUnk.get(elem)[size - 1], new Integer(1));
                                    } else {
                                        int valor = ((Integer) confusionMatrixTmp
                                                .get("C " + dataUnk.get(elem)[size - 1])).intValue();
                                        confusionMatrixTmp.put("C " + dataUnk.get(elem)[size - 1],
                                                new Integer(valor + 1));
                                    }
                                }
                            }
                            // ********* identify if the valid cluster is an extension or a novelty pattern
                            // to find the closest cluster to the new valid cluster
                            ArrayList<String> results = identClosestCluster(clusterUnk, threshold);
                            double distance = Double.parseDouble(results.get(0));
                            double thresholdValue = Double.parseDouble(results.get(1));
                            String category = results.get(2);
                            String classLabel = results.get(3);

                            String text = "";
                            // if the distance (Euclidean) between the centroid of the new valid cluster and
                            // its closest cluster is less than a threshold
                            if (distance < thresholdValue) {// then: the new valid cluster in an extension of a concept
                                // extension of a class learned offline
                                if ((category.equalsIgnoreCase("normal")) || (category.equalsIgnoreCase("ext"))) {
                                    updateModel(clusterUnk, classLabel, "ext");
                                    text = "Thinking " + "Extension: " + "C " + classLabel + " - "
                                            + (int) clusterUnk.getSize() + " examples";
                                }
                                // extension of a novelty pattern learned online
                                else {
                                    updateModel(clusterUnk, classLabel, "extNov");
                                    text = "Thinking " + "NoveltyExtension: " + "N " + classLabel + " - "
                                            + (int) tmpModelUnk.get(cluster).getSize() + " examples";
                                }
                            } else {
                                // else: the new valid cluster is a novelty pattern
                                updateModel(clusterUnk, Integer.toString(Novelties.size() + 1), "nov");
                                // if the valid clusters is really identified as novelty (may be a novelty
                                // intercepte another novelty and thus it is considered an extension
                                if (model.get(model.size() - 1).getLblClasse()
                                        .compareToIgnoreCase(Integer.toString(Novelties.size() + 1)) == 0) {
                                    // verify if the new valid cluster is, in fact, a recurrence of a known class
                                    if (verifyClassRecurrence(clusterUnk)) {
                                        if (clusterUnk.getCategory().compareToIgnoreCase("ext") == 0)
                                            text = "Thinking " + "Extension:" + "C "
                                                    + model.get(model.size() - 1).getLblClasse() + " - "
                                                    + (int) tmpModelUnk.get(cluster).getSize() + " examples";
                                        else
                                            text = "Thinking " + "NoveltyExtension: " + "N "
                                                    + model.get(model.size() - 1).getLblClasse() + " - "
                                                    + (int) tmpModelUnk.get(cluster).getSize() + " examples";
                                        // System.out.println("Recurrence of the class"
                                        // +(tmpModelUnk.get(cluster).getLblClasse())+" -
                                        // "+(int)tmpModelUnk.get(cluster).getSize()+" examples");
                                    } else {
                                        // the class label of a new valid cluster considered as a novelty is a
                                        // sequential number
                                        Novelties.add(Novelties.size() + 1 + "");
                                        text = "ThinkingNov: " + "Novidade " + (Novelties.size()) + " - "
                                                + (int) tmpModelUnk.get(cluster).getSize() + " examples";
                                    }
                                } else {
                                    text = "Thinking " + "NoveltyExtension: " + "N "
                                            + model.get(model.size() - 1).getLblClasse() + " - "
                                            + (int) tmpModelUnk.get(cluster).getSize() + " examples";
                                }
                            }
                            fileOut.write(text);
                            fileOut.write("\n");
                            av.updateConfusionMatrix(text, confusionMatrixTmp);

                        } // fim do grupo valido
                          // Se o grupo foi considerado invalido por ser muito esparso
                        else {
                            // Aumentar o contador deste tipo de falha, para a configuracao autom�tica de k
                            temp_count_toosparse++;
                        }
                    } // Fim tem o numero minimo de exemplos
                      // Se o grupo foi considerado inv�lido por nao ter o numero minimo de exemplos
                    else {
                        // Aumentar o contador deste tipo de falha, para a configura��o autom�tica de k
                        temp_count_toofewex++;
                    }
                } // Fim para cada grupo candidato

                // ********** Adaptacao Automatica de k **********
                count_k = adaptationK(flgTodosInvalidos, temp_count_toosparse, temp_count_toofewex, count_k,
                        dataUnk.size());

                // remover os elementos com o -1
                int count_rem = 0;
                for (int g = 0; g < tmpRemove.length; g++) {
                    if (tmpRemove[g] == -1) {
                        dataUnk.remove(g - count_rem);
                        count_rem++;
                    }
                }
            } // Fim o numero de exemplos eh suficiente
            else { // Se o numero de exemplos nao eh suficiente
                if (count_k > 2) {
                    count_k--;
                }
            }
        } // Fim exemplo nao identificado como unknown
        return count_k;
    }

    /********************* Online ****************************************************/
    public void online(ArrayList<String> classesOffline, Evaluation av) throws IOException {
        int countEx = 0;
        String classeEx;
        int count_k = 2;

        ArrayList<String> NoveltyPatterns = new ArrayList<String>();

        String filenameOut = outputDirectory + "\\results";
        av.initializeConfusionMatrix(classesOffline);

        String[] dataEx;
        BufferedReader fileOnline = new BufferedReader(new FileReader(new File(filenameOnline)));
        String line;
        int size = 0;

        // obtaining information about the clusters obtained offline (used to verify if
        // a new cluster is valid)
        ArrayList<Double> vectorMeasuresModelOffline = new ArrayList<Double>();
        for (int m = 0; m < model.size(); m++) {
            if (model.get(m).getCategory().equalsIgnoreCase("normal")) {
                if (validationCriterion.equalsIgnoreCase("dec")) {
                    vectorMeasuresModelOffline.add(model.get(m).getMeanDistance());
                }
            }
        }
        // reading data of online phase
        while ((line = fileOnline.readLine()) != null) {
            countEx++;
            if ((countEx % 10000) == 0)
                System.out.println(countEx);

            timestamp++;
            dataEx = line.split(",");
            size = dataEx.length;
            classeEx = dataEx[size - 1];
            double[] data_ex_double = new double[size - 1];
            for (int j = 0; j < size - 1; j++) {
                data_ex_double[j] = Double.valueOf(dataEx[j]);
            }
            // printing..
            String text = "Ex: " + countEx + "\t Classe Real: " + classeEx + "\t Classe MINAS: ";

            // ************* classifying a new instance
            // *********************************************
            count_k = classify(av, count_k, dataEx, text, countEx, vectorMeasuresModelOffline, NoveltyPatterns);
            // ***********fim da classificacao da instancia*****************

            // put the inative clusters (if they do not receive examples for x timestamps)
            // in a sleepMemory
            if (countEx % thresholdForgettingPast == 0)
                putClustersSleepModeMem(countEx, thresholdForgettingPast);
        } // # end of online phase
        fileOnline.close();
        fileOut.close();

        av.printResultsGraph(filenameOut);
    }

    /********************* adaptationK ***********************************************/
    public int adaptationK(int flgTodosInvalidos, int temp_count_toosparse, int temp_count_toofewex, int count_k,
            int tamDataUnk) {
        if (flgTodosInvalidos == 1) {
            // Se o motivo mais frequente eh que os grupos sao muito esparsos
            if (temp_count_toosparse > temp_count_toofewex) {
                // Se k eh menor do que um limite superior para k, no qual cada grupo tem em
                // media o numero minimo de exemplos
                if (count_k < ((float) tamDataUnk / minExCluster)) {
                    // Incrementar k
                    count_k++;

                }
            } else {
                // Se o motivo mais frequente eh que os grupos tem poucos exemplos
                if (temp_count_toosparse < temp_count_toofewex) {
                    // Se k eh maior que 2
                    if (count_k > 2) {
                        count_k--; // Decrementar k
                    }
                } else {
                    // Se os dois motivos sao igualmente frequentes, manter o valor de k
                    if (temp_count_toosparse == temp_count_toofewex) {
                        // Se tratamento dado a cada exemplo deve ser armazenado
                    }
                }
            }
        }
        return count_k;
    }

    /********************* updateModel ***********************************************/
    public void updateModel(Cluster validCluster, String classLabel, String category) {
        // updating de decision model, adding a new valid cluster
        validCluster.setCategory(category);
        validCluster.setLblClasse(classLabel);
        model.add(validCluster);

        ArrayList<double[]> centers = new ArrayList<double[]>();
        ArrayList<String> novelty = new ArrayList<String>();
        ArrayList<Double> radius = new ArrayList<Double>();

        // case the new valid cluster is a novelty pattern
        // to verify if it intercept someone of the existing novelty clusters
        // if so: it an extension --> not a novelty patter
        if (category.equalsIgnoreCase("nov")) {
            for (int i = 0; i < model.size(); i++) {
                String cat = model.get(i).getCategory();
                if (cat.equalsIgnoreCase("nov")) {
                    novelty.add(model.get(i).getLblClasse());
                    radius.add(model.get(i).getRadius());
                    centers.add(model.get(i).getCenter());
                }
            }
        }
        if (!centers.isEmpty()) {
            double temp_dist = 0.0;
            double[] center = validCluster.getCenter();
            for (int k = 0; k < centers.size() - 1; k++) {
                temp_dist = KMeansMOAModified.distance(center, centers.get(k));
                if (temp_dist < (radius.get(k) + validCluster.getRadius())) {
                    model.get(model.size() - 1).setLblClasse(novelty.get(k));
                    model.get(model.size() - 1).setCategory("extNov");
                }
            }
        }
    }

    /********************* identClosestCluster ***************************************/
    public ArrayList<String> identClosestCluster(Cluster validCluster, double threshold) {
        // find the closest cluster to the new valid cluster
        double minDist = 0;
        minDist = KMeansMOAModified.distance(model.get(0).getCenter(), validCluster.getCenter());
        int pos = 0;
        double dist = 0;

        for (int i = 1; i < model.size(); i++) {
            dist = KMeansMOAModified.distance(model.get(i).getCenter(), validCluster.getCenter());
            if (dist < minDist) {
                minDist = dist;
                pos = i;
            }
        }
        // compute threshold: mean distance between the examples of the cluster to the
        // centroid multiplied by a factor (user input)
        double vthreshold = model.get(pos).getMeanDistance() * threshold;
        String category = model.get(pos).getCategory();
        String classLabel = model.get(pos).getLblClasse();

        ArrayList<String> results = new ArrayList<String>();
        results.add(Double.toString(minDist));
        results.add(Double.toString(vthreshold));
        results.add(category);
        results.add(classLabel);
        return results;
    }

    /********************* createTmpModelUnk *****************************************/
    public ArrayList<Cluster> createTmpModelUnk(int k, int[] vectorResClustering) throws IOException {
        ArrayList<Cluster> modelUnk = null;
        if (algClusteringOnl.equals("kmeans")) {
            modelUnk = createModelKMeans(null, k, null, dataUnk, vectorResClustering);
        }

        // in order to execute de clustream algorithm, the data needs to be stored in a
        // file
        if (algClusteringOnl.equals("clustream")) {
            String filenameTmp = "caminho" + "temp.csv";
            FileWriter fileOutTmp = new FileWriter(filenameTmp);
            for (int i = 0; i < dataUnk.size(); i++) {
                for (int j = 0; j < dataUnk.get(i).length - 1; j++)
                    fileOutTmp.write(dataUnk.get(i)[j] + ",");
                fileOutTmp.write(dataUnk.get(i)[dataUnk.get(i).length - 1]);
                fileOutTmp.write("\n");
            }
            fileOutTmp.close();
            modelUnk = createModelClustream(filenameTmp, "", vectorResClustering);
        }
        return (modelUnk);
    }

    /********************* createModelKMeans *****************************************/
    public ArrayList<Cluster> createModelKMeans(String filename, int k, String cl, ArrayList<String[]> data,
            int[] clusters) throws NumberFormatException, IOException {
        String line;
        int cont = 0;
        int lineSize = 0;
        ArrayList<Cluster> clusterSet = new ArrayList<Cluster>();
        List<ClustreamKernelMOAModified> elemList = new LinkedList<ClustreamKernelMOAModified>();

        // if the data are not in a file
        if (filename == null) {
            int j = 0;
            double lineDouble[];
            while (j < data.size()) {
                lineSize = data.get(j).length;
                String[] lineString = new String[lineSize];
                lineString = data.get(j);
                lineDouble = new double[lineSize - 1];
                for (int i = 0; i < lineSize - 1; i++) {
                    lineDouble[i] = Double.parseDouble(lineString[i]);
                }
                Instance inst = new DenseInstance(1, lineDouble);
                cont++;
                // list with the element to be clustered
                elemList.add(new ClustreamKernelMOAModified(inst, lineDouble.length, cont));
                j++;
            }
        }
        // if the data are in a file
        else {
            // reading the elements from teh file and keeping a list
            BufferedReader file = new BufferedReader(new FileReader(new File(filename)));
            while ((line = file.readLine()) != null) {
                String lineString[] = line.split(",");
                lineSize = lineString.length - 1;
                double lineDouble[] = new double[lineSize];
                for (int i = 0; i < lineSize; i++) {
                    lineDouble[i] = Double.parseDouble(lineString[i]);
                }
                Instance inst = new DenseInstance(1, lineDouble);
                cont++;
                // list with the element to be clustered
                elemList.add(new ClustreamKernelMOAModified(inst, lineDouble.length, cont));
            }
            file.close();
        }

        clusters = new int[elemList.size()];
        ClustreamKernelMOAModified[] initialCenters = new ClustreamKernelMOAModified[k];
        for (int i = 0; i < k; i++) {
            initialCenters[i] = elemList.get(i);
        }

        // execution of the KMeans
        // variable to store the results of the Kmeans
        double soma[] = new double[1];
        Clustering centers;
        ArrayList<Integer> clusterSize = new ArrayList<Integer>();
        int elemCluster[] = new int[elemList.size()];
        ArrayList<Double> radius = new ArrayList<Double>();
        ArrayList<Double> meanDistance = new ArrayList<Double>();

        KMeansMOAModified cm = new KMeansMOAModified();
        centers = cm.kMeans2(initialCenters, elemList, soma, clusterSize, elemCluster, radius, meanDistance);

        for (int g = 0; g < elemCluster.length; g++) {
            clusters[g] = elemCluster[g];
        }
        for (int w = 0; w < k; w++) {
            Cluster clus = new Cluster(meanDistance.get(w), centers.get(w).getCenter(), clusterSize.get(w),
                    radius.get(w), cl, "normal", timestamp);
            clusterSet.add(clus);
        }
        return clusterSet;
    }

    /********************* createModelClustream **************************************/
    public ArrayList<Cluster> createModelClustream(String filename, String cl, int[] vectorResClustering)
            throws NumberFormatException, IOException {
        ArrayList<double[]> centers = null;
        ArrayList<Cluster> clusterSet = new ArrayList<Cluster>();
        ClustreamOffline jc = new ClustreamOffline();

        // executing the clustream offline
        centers = jc.CluStreamOff(cl, filename, numMicro, flagMicroClusters);

        // results
        double[] size = jc.getClusterSize();
        double[] radius = jc.getRadius();
        double[] meanDistance = jc.meanDistance();
        String[] classLabel = jc.getClusterClass();

        if (currentState.compareTo("online") == 0) {
            int tmp[] = jc.getClusterExample();
            ;
            for (int i = 0; i < tmp.length; i++)
                vectorResClustering[i] = tmp[i];
        }

        // one class is represented by a set of Clusters
        // creating a clusterModel for each cluster
        for (int w = 0; w < size.length; w++) {
            Cluster clus = new Cluster(meanDistance[w], centers.get(w), size[w], radius[w], classLabel[w], "normal",
                    timestamp);
            clusterSet.add(clus);
        }
        return clusterSet;
    }

    /********************* identifyExample *******************************************/
    public String[] identifyExample(double[] dataEx) {
        double dist = 0.0;
        double minDist = Double.MAX_VALUE;
        int pos = 0;
        String[] vectorResults = new String[2];

        for (int j = 0; j < model.size(); j++) {
            dist = KMeansMOAModified.distance(model.get(j).getCenter(), dataEx);
            if (dist <= minDist) {
                minDist = dist;
                pos = j;
            }
        }
        try {
            if (minDist < model.get(pos).getRadius()) {
                vectorResults[0] = model.get(pos).getLblClasse();
                vectorResults[1] = model.get(pos).getCategory();
                model.get(pos).setTime(timestamp);
                return (vectorResults);
            }
        } catch (Exception E) {
            System.out.println("Accessed Position: " + pos);
            System.out.println("Model Size: " + model.size());

        }

        return (null);
    }

    /********************* putClustersSleepModeMem ***********************************/
    public void putClustersSleepModeMem(int timestamp, int T) {
        for (int i = 0; i < model.size(); i++) {
            if (model.get(i).getTime() < (timestamp - T)) {
                SleepModeMem.add(model.get(i));
                model.remove(i);
            }
        }

    }

    /********************* verifyClassRecurrence *************************************/
    public boolean verifyClassRecurrence(Cluster validCluster) {
        double dist, minDist;
        if (SleepModeMem.size() > 0) {
            minDist = KMeansMOAModified.distance(SleepModeMem.get(0).getCenter(), validCluster.getCenter());
            int pos = 0;

            for (int i = 1; i < SleepModeMem.size(); i++) {
                dist = KMeansMOAModified.distance(SleepModeMem.get(i).getCenter(), validCluster.getCenter());
                if (dist < minDist) {
                    minDist = dist;
                    pos = i;
                }
            }
            double vthreshold = SleepModeMem.get(pos).getMeanDistance() * threshold;
            if ((minDist * minDist) <= vthreshold) {
                if ((SleepModeMem.get(pos).getCategory().equalsIgnoreCase("normal"))
                        || (SleepModeMem.get(pos).getCategory().equalsIgnoreCase("ext")))
                    validCluster.setCategory("ext");
                else
                    validCluster.setCategory("extNov");
                validCluster.setLblClasse(SleepModeMem.get(pos).getLblClasse());
                return true;
            }
            return false;
        }
        return false;
    }

    /********************* funcao max ************************************************/
    public double max(ArrayList<Double> L) {
        double maior = L.get(0);
        for (int i = 0; i < L.size(); i++)
            if (L.get(i) > maior)
                maior = L.get(i);
        return maior;
    }

    /********************* execution *************************************************/
    public void execution() throws IOException {
        Evaluation av = new Evaluation(flagEvaluationType);
        // create_FileOut();
        String nameFileOut = outputDirectory + "\\results";
        String nameFileOutClasses = outputDirectory + "\\results" + "Classes";
        fileOut = new FileWriter(new File(nameFileOut), false);
        fileOutClasses = new FileWriter(new File(nameFileOutClasses), false);

        fileOut.write("Results");
        fileOut.write("\n\n \n\n");
        //
        System.out.println("\n Processing " + outputDirectory + "_" + " initial phase...\n\n");
        timestamp++;
        SleepModeMem = new ArrayList<Cluster>();
        dataUnk = new ArrayList<String[]>();
        System.out.println("********************** Offline phase ****************************");
        currentState = "offline";
        ArrayList<String> classesOffline = offline();
        System.out.println("********************** Online phase****************************");
        currentState = "online";
        online(classesOffline, av);
        System.out.println("********************** Results ****************************");
        // av.ExibeResultadosFolds(par_outdir + "Res.csv");
    }

    /********************* printModelInformation **************************************/
    public void printModelInformation(double clusterSize[], double clusterRadius[], double meandDistance[]) {
        int j;
        System.out.print("\n Size of each cluster: ");
        for (j = 0; j < clusterSize.length; j++) {
            System.out.print(clusterSize[j] + " ");
        }

        System.out.print("\n Radius of each cluster: ");
        for (j = 0; j < clusterRadius.length; j++) {
            System.out.print(clusterRadius[j] + " ");
        }

        System.out.print("\n Mean distance of examples to centroid for each cluster: ");
        for (j = 0; j < meandDistance.length; j++) {
            System.out.print(meandDistance[j] + " ");
        }
        System.out.println("\n");
    }

    /********************* funcao Main************************************************/
    public static void main(String[] args) throws IOException {
        MINAS m;
        // m = new MINAS("balancescale_nor1", "C:\\Users\\Elaine\\Documents\\", "clustream", 1.1, "data_s_n_f_s");
        // m = new MINAS("iris_nor1", "C:\\Users\\Elaine\\Documents\\", "kmeans", 1.1, "data_s_n_f_s", 10);
        // m = new MINAS("MOA3", "C:\\Users\\Elaine\\Documents\\", "clustream", "clustream", 2.0, "data_s_n_f_s", 1, 0);
        // m = new MINAS("SynDMenor", "C:\\Users\\Elaine\\Documents\\", "kmeans", 2.0, "data_s_n_f_s", 1);
        // m = new MINAS("SynDMenor", "C:\\Users\\Elaine\\Documents\\", "clustream", 1.1, "data_s_n_f_s", 1);
        // m = new MINAS("KDDTe", "C:\\Users\\Elaine\\Documents\\", "clustream", "clustream", 3.0, "data_s_n_f_s", 1);
        // m = new MINAS("KDDTe5Classes", "D:\\TestesMinas\\", "clustream", "clustream", 2.0, "data_s_n_f_s", 1, 1);
        // m = new MINAS("fcTe", "C:\\Users\\Elaine\\Documents\\", "clustream", "clustream", 1.1, "data_s_n_f_s", 1, 1);
        String fileOff = "C:\\Users\\Elaine\\Documents\\data_s_n_f_s\\covtypeOrigNorm_off";
        String fileOnl = "C:\\Users\\Elaine\\Documents\\data_s_n_f_s\\covtypeOrigNorm_onl";
        String outDirec = "E:\\resultados";
        String algOff = "clustream";
        String algOnl = "clustream";
        double threshold = 2.0;
        int evaluationType = 1;
        int thresholdForgetPast = 10000;
        int nMicro = 100;
        boolean flag = true;
        m = new MINAS(fileOff, fileOnl, outDirec, algOff, algOnl, threshold, evaluationType, thresholdForgetPast, nMicro, flag);
        m.execution();
    }
}
