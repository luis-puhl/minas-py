package NoveltyDetection;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import moa.cluster.CFCluster;
import moa.cluster.Cluster;
import moa.cluster.Clustering;
import moa.cluster.SphereCluster;

public class KMeansMOAModified {
    public static int bestK;

    public Clustering kMeans2(Cluster[] centers, List<? extends Cluster> data, double soma[],
            ArrayList<Integer> clusterSize, int elemCluster[], ArrayList<Double> maxDistance,
            ArrayList<Double> meanDistance) {
        int k = centers.length;

        int dimensions = centers[0].getCenter().length;

        ArrayList<ArrayList<Cluster>> clustering = new ArrayList<ArrayList<Cluster>>();
        for (int i = 0; i < k; i++) {
            clustering.add(new ArrayList<Cluster>());
        }

        int repetitions = 100;
        double sum = 0;
        do {
            // Assign points to clustersf
            int cont = 0;
            sum = 0;
            for (Cluster point : data) {
                double minDistance = distance(point.getCenter(), centers[0].getCenter());
                int closestCluster = 0;
                for (int i = 1; i < k; i++) {
                    double distance = distance(point.getCenter(), centers[i].getCenter());
                    if (distance < minDistance) {
                        closestCluster = i;
                        minDistance = distance;
                    }
                }
                sum += minDistance;
                clustering.get(closestCluster).add(point);

                if (repetitions == 0) {
                    elemCluster[cont] = closestCluster;
                }
                cont++;
            }
            // Calculate new centers and clear clustering lists
            SphereCluster[] newCenters = new SphereCluster[centers.length];
            for (int i = 0; i < k; i++) {
                newCenters[i] = calculateCenter(clustering.get(i), dimensions);
                if (repetitions != 0) {
                    clustering.get(i).clear();
                }
            }
            centers = newCenters;
            repetitions--;
        } while (repetitions >= 0);

        // keeping a vector that contains in each position, the number of elements of
        // the clusters
        for (int i = 0; i < clustering.size(); i++)
            clusterSize.add(clustering.get(i).size());

        getRadiusMeanDistance(clustering, new Clustering(centers), maxDistance, meanDistance);
        soma[0] = sum;
        return new Clustering(centers);
    }

    public void getRadiusMeanDistance(
        ArrayList<ArrayList<Cluster>> clustering, Clustering centers,
        ArrayList<Double> maxDistance, ArrayList<Double> meanDistance
    ) {
        int k = centers.size();
        double[] centro;
        double maiorDist;
        double[] elem;
        double soma, distancia, mean;

        for (int i = 0; i < k; i++) { // para cada macro-cluster
            // clustering eh o resultado do kmeans
            centro = centers.get(i).getCenter(); // obter o centro do macro-cluster
            maiorDist = 0;
            mean = 0.0;
            for (int j = 0; j < clustering.get(i).size(); j++) { // para cada elemento no macro-cluster
                elem = clustering.get(i).get(j).getCenter();
                soma = 0;
                for (int l = 0; l < elem.length; l++) { // distancia do elem ao centro
                    soma = soma + Math.pow(centro[l] - elem[l], 2);
                }
                distancia = Math.sqrt(soma);
                mean = mean + distancia;
                if (distancia > maiorDist) // procurando pelo elem cuja distancia e a maior
                    maiorDist = distancia;
            }
            maxDistance.add(maiorDist);
            meanDistance.add(mean / clustering.get(i).size());
        }
    }

    /*******************************************************************************
     ******************** OMRk ******************************************************
     ********************************************************************************/
    public static Clustering OMRk(Clustering microClusteringResult, int algCentroidChoice,
            ArrayList<ArrayList<Integer>> elemMacroCluster) {
        double silhouetteValue = 0.0, maxSilhueta = 0.0;
        maxSilhueta = Double.MAX_VALUE;
        Clustering bestPartition = new Clustering();
        ArrayList<CFCluster> microclusters = new ArrayList<CFCluster>();
        Cluster[] centers = null;
        ArrayList<ArrayList<Integer>> grupo;

        for (int i = 0; i < microClusteringResult.size(); i++) {
            if (microClusteringResult.get(i) instanceof CFCluster) {
                microclusters.add((CFCluster) microClusteringResult.get(i));
            }
        }

        for (int k = 2; k <= (int) 2 * Math.sqrt(microclusters.size()); k++) {
            // System.out.print("\n K:" + valorK + " ");
            for (int i = 0; i < 10; i++) {
                switch (algCentroidChoice) {
                case 0:
                    centers = sequentialCenters(microclusters, k);
                    break;
                }
                double cost[] = new double[1];
                Clustering kMeansResult = kMeansNotEmpty(centers, microclusters, cost);
                System.out.print(" v: " + cost[0]);
                grupo = new ArrayList<ArrayList<Integer>>();

                silhouetteValue = calculateSilhouette(kMeansResult, microclusters, grupo);
                if ((k == 2) && (i == 0))
                    maxSilhueta = silhouetteValue;
                // System.out.print(" s: " + silhouetteValue + " ");
                if (silhouetteValue >= maxSilhueta) {
                    maxSilhueta = silhouetteValue;
                    bestK = k;
                    if (bestPartition.size() > 0) {
                        int tam = bestPartition.size();
                        for (int j = 0; j < tam; j++)
                            bestPartition.remove(0);
                    }

                    for (int j = 0; j < kMeansResult.size(); j++) {
                        bestPartition.add(kMeansResult.get(j));
                    }
                }
            }
        }
        // System.out.println("\n The best value to K: " + melhorK);
        ArrayList<ArrayList<Integer>> macroClusteringAux = new ArrayList<ArrayList<Integer>>();
        for (int i = 0; i < bestK; i++) {
            macroClusteringAux.add(new ArrayList<Integer>());
        }

        CFCluster[] res = new CFCluster[bestK];
        int counter = 0;
        for (CFCluster microcluster : microclusters) {
            // Find closest kMeans cluster
            double minDistance = Double.MAX_VALUE;
            int closestCluster = 0;

            for (int i = 0; i < bestK; i++) {
                double distance = distance(bestPartition.get(i).getCenter(), microcluster.getCenter());

                if (distance < minDistance) {
                    closestCluster = i;
                    minDistance = distance;
                }
            }
            if (res[closestCluster] == null) {
                res[closestCluster] = (CFCluster) microcluster.copy();
            } else {
                res[closestCluster].add(microcluster);
            }
            macroClusteringAux.get(closestCluster).add((int) counter);
            counter++;
        }

        // Clean up res
        int count = 0;
        for (int i = 0; i < res.length; i++) {
            if (res[i] != null)
                ++count;
        }

        CFCluster[] cleaned = new CFCluster[count];
        count = 0;
        for (int i = 0; i < res.length; i++) {
            if (res[i] != null) {
                cleaned[count++] = res[i];
                elemMacroCluster.add(macroClusteringAux.get(i));
            }
        }
        return new Clustering(cleaned);
    }

    /*******************************************************************************
     ******************** calculateSilhouette ***************************************
     ********************************************************************************/
    public static double calculateSilhouette(Clustering clusters, ArrayList<CFCluster> microclusters,
            ArrayList<ArrayList<Integer>> elemMacroCluster) {
        int numFCluster = clusters.size();
        double silhouette = 0;
        double pointSilhouette = 0;
        int clusterElem[] = new int[microclusters.size()];

        for (int i = 0; i < numFCluster; i++)
            elemMacroCluster.add(new ArrayList<Integer>());

        for (int i = 0; i < microclusters.size(); i++) {
            double minDistance = distance(microclusters.get(i).getCenter(), clusters.get(0).getCenter());
            int closestCluster = 0;
            for (int j = 1; j < numFCluster; j++) {
                double distance = distance(microclusters.get(i).getCenter(), clusters.get(j).getCenter());
                if (distance < minDistance) {
                    closestCluster = j;
                    minDistance = distance;
                }
            }
            elemMacroCluster.get(closestCluster).add(i);
            clusterElem[i] = closestCluster;

        }

        for (int p = 0; p < clusterElem.length; p++) {
            Integer ownClusters = clusterElem[p];

            double[] distanceByClusters = new double[numFCluster - 1];
            int pos = 0;
            for (int fc = 0; fc < numFCluster; fc++) {
                if (fc != ownClusters) {
                    double distance = distance(microclusters.get(p).getCenter(), clusters.get(fc).getCenter());
                    distanceByClusters[pos] = distance;
                    pos++;
                }
            }
            Arrays.sort(distanceByClusters);
            double distancePointToCluster = distance(microclusters.get(p).getCenter(),
                    clusters.get(ownClusters).getCenter());
            double distancePointToCloserCluster = distanceByClusters[0];

            pointSilhouette += (distancePointToCloserCluster - distancePointToCluster)
                    / Math.max(distancePointToCloserCluster, distancePointToCluster);
        }
        silhouette = pointSilhouette / microclusters.size();
        return silhouette;
    }

    /*******************************************************************************
     ******************** kMeansNaoVazio ********************************************
     ********************************************************************************/
    public static Clustering kMeansNotEmpty(Cluster[] centers, List<? extends Cluster> data, double cost[]) {
        int k = centers.length;
        int dimensions = centers[0].getCenter().length;

        ArrayList<ArrayList<Cluster>> clustering = new ArrayList<ArrayList<Cluster>>();
        for (int i = 0; i < k; i++) {
            clustering.add(new ArrayList<Cluster>());
        }

        int repetitions = 100;
        double sum = 0;

        while (repetitions-- >= 0) {
            // Assign points to clusters
            sum = 0;
            for (Cluster point : data) {
                double minDistance = distance(point.getCenter(), centers[0].getCenter());
                int closestCluster = 0;
                for (int i = 1; i < k; i++) {
                    double distance = distance(point.getCenter(), centers[i].getCenter());
                    if (distance < minDistance) {
                        closestCluster = i;
                        minDistance = distance;
                    }
                }
                sum += minDistance;
                clustering.get(closestCluster).add(point);
            }

            // Calculate new centers and clear clustering lists
            SphereCluster[] newCenters = new SphereCluster[centers.length];
            for (int i = 0; i < k; i++) {
                int posMax1 = 0, posMax2 = 0;
                if (clustering.get(i).size() == 0) { // cluster do not have element
                    System.out.println("************size: 0*************");
                    // search for the cluster with the biggest radius
                    // posMax1: cluster with the biggest radius
                    // posMax2: element of the cluster more distant from the centroid
                    double maxRadius = 0;
                    double distance;
                    for (int j = 0; j < k; j++) {
                        if (i != j) {
                            for (int l = 0; l < clustering.get(j).size(); l++) {
                                distance = distance(clustering.get(j).get(l).getCenter(), centers[j].getCenter());
                                if (distance > maxRadius) {
                                    maxRadius = distance;
                                    posMax1 = j;
                                    posMax2 = l;
                                }
                            }
                        }
                    }
                    // creating a new cluster with the element more distant of the centroid
                    // criando um novo grupo com este elemento mais distance
                    clustering.get(i).add(clustering.get(posMax1).get(posMax2));
                    clustering.get(posMax1).remove(posMax2);

                    // re-distributing the element of the cluster between the two new clusters
                    for (int n = 0; n < clustering.get(posMax1).size(); n++) {
                        double distance1 = distance(clustering.get(posMax1).get(n).getCenter(),
                                centers[posMax1].getCenter());
                        double distance2 = distance(clustering.get(posMax1).get(n).getCenter(),
                                clustering.get(i).get(0).getCenter());
                        if (distance2 < distance1) {
                            clustering.get(i).add(clustering.get(posMax1).get(n));
                            clustering.get(posMax1).set(n, null);
                        }
                    }
                    for (int z = 0; z < clustering.get(posMax1).size(); z++)
                        if (clustering.get(posMax1).get(z) == null) {
                            clustering.get(posMax1).remove(z);
                            z--;
                        }
                    // re-calculating the centroid
                    newCenters[posMax1] = calculateCenter(clustering.get(posMax1), dimensions);
                }
                newCenters[i] = calculateCenter(clustering.get(i), dimensions);
            }
            centers = newCenters;
            for (int i = 0; i < k; i++)
                clustering.get(i).clear();
        }
        cost[0] = sum;
        return new Clustering(centers);
    }

    /*******************************************************************************
     ******************** calculateCenter *******************************************
     ********************************************************************************/
    private static SphereCluster calculateCenter(ArrayList<Cluster> cluster, int dimensions) {
        double[] res = new double[dimensions];
        for (int i = 0; i < res.length; i++) {
            res[i] = 0.0;
        }

        if (cluster.size() == 0) {
            return new SphereCluster(res, 0.0);
        }

        for (Cluster point : cluster) {
            double[] center = point.getCenter();
            for (int i = 0; i < res.length; i++) {
                res[i] += center[i];
            }
        }

        // Normalize
        for (int i = 0; i < res.length; i++) {
            res[i] /= cluster.size();
        }

        // Calculate radius
        double radius = 0.0;
        for (Cluster point : cluster) {
            double dist = distance(res, point.getCenter());
            if (dist > radius) {
                radius = dist;
            }
        }

        return new SphereCluster(res, radius);
    }

    /*******************************************************************************
     ******************** sequentialCenters******************************************
     ********************************************************************************/
    public static Cluster[] sequentialCenters(ArrayList<CFCluster> clustering, int k) {
        Cluster[] centers = new Cluster[k];

        for (int i = 0; i < centers.length; i++) {
            centers[i] = clustering.get(i);
        }
        return centers;
    }

    /*******************************************************************************
     ******************** distance************************************************
     ********************************************************************************/
    public static double distance(double[] pointA, double[] pointB) {
        double distance = 0.0;
        for (int i = 0; i < pointA.length; i++) {
            double d = pointA[i] - pointB[i];
            distance += d * d;
        }
        return Math.sqrt(distance); // distance;
    }
}
