package NoveltyDetection;

import java.util.ArrayList;
import java.util.Random;
import moa.cluster.CFCluster;
import moa.clusterers.clustream.Clustream;
import weka.core.DenseInstance;
import weka.core.Instance;

/**
 *
 */
public class ClustreamKernelMOAModified extends CFCluster {
    private final static double EPSILON = 0.00005;
    public static final double MIN_VARIANCE = 1e-50;

    protected double LST;
    protected double SST;
    String classe;
    // ArrayList<String> classes=new ArrayList<String>();
    // ArrayList<Integer> nroExamples= new ArrayList<Integer>();

    public ClustreamKernelMOAModified(Instance instance, int dimensions, long timestamp) {
        super(instance, dimensions);
        this.LST = timestamp;
        this.SST = timestamp * timestamp;
    }

    public ClustreamKernelMOAModified(Instance instance, int dimensions, long timestamp, String classe) {
        super(instance, dimensions);
        this.LST = timestamp;
        this.SST = timestamp * timestamp;
        this.classe = classe;
        /*
         * if (classes.size() == 0){ classes.add(classe); nroExamples.add(1); } else{
         * int pos = classes.indexOf(classe); if (pos == -1){ classes.add(classe);
         * nroExamples.add(1); } else{ nroExamples.set(pos, nroExamples.get(pos)+1); } }
         */

    }

    public ClustreamKernelMOAModified(ClustreamKernelMOAModified cluster) {
        super(cluster);
        this.LST = cluster.LST;
        this.SST = cluster.SST;
    }

    public void insert(Instance instance, long timestamp) {
        N++;
        LST += timestamp;
        SST += timestamp * timestamp;

        for (int i = 0; i < instance.numValues(); i++) {
            LS[i] += instance.value(i);
            SS[i] += instance.value(i) * instance.value(i);
        }
    }

    public void add(ClustreamKernelMOAModified other) {
        assert (other.LS.length == this.LS.length);
        this.N += other.N;
        this.LST += other.LST;
        this.SST += other.SST;

        for (int i = 0; i < LS.length; i++) {
            this.LS[i] += other.LS[i];
            this.SS[i] += other.SS[i];
        }
    }

    public double getRelevanceStamp() {
        if (N < 2 * Clustream.m)
            return getMuTime();

        return getMuTime() + getSigmaTime() * getQuantile(((double) Clustream.m) / (2 * N));
    }

    private double getMuTime() {
        return LST / N;
    }

    private double getSigmaTime() {
        return Math.sqrt(SST / N - (LST / N) * (LST / N));
    }

    private double getQuantile(double z) {
        assert (z >= 0 && z <= 1);
        return Math.sqrt(2) * inverseError(2 * z - 1);
    }

    @Override
    public double getRadius() {
        // trivial cluster
        if (N == 1)
            return 0;

        // return getDeviation()*1.6;
        return getDeviationElaine() * 2.0;
        // return getDeviation()*2.0;
    }

    private double getDeviation() {
        double[] variance = getVarianceVector();
        double sumOfDeviation = 0.0;
        for (int i = 0; i < variance.length; i++) {
            double d = Math.sqrt(variance[i]);
            sumOfDeviation += d;
        }
        return sumOfDeviation / variance.length;
    }

    private double getDeviationElaine() {
        double[] variance = getVarianceVector();
        double sumOfDeviation = 0.0;
        for (int i = 0; i < variance.length; i++) {
            sumOfDeviation += variance[i];
        }
        return Math.sqrt(sumOfDeviation);
    }

    /**
     * @return this kernels' center
     */
    @Override
    public double[] getCenter() {
        assert (!this.isEmpty());
        double res[] = new double[this.LS.length];
        for (int i = 0; i < res.length; i++) {
            res[i] = this.LS[i] / N;
        }
        return res;
    }

    /**
     * See interface <code>Cluster</code>
     * 
     * @param point
     * @return
     */
    @Override
    public double getInclusionProbability(Instance instance) {
        // trivial cluster
        if (N == 1) {
            double distance = 0.0;
            for (int i = 0; i < LS.length; i++) {
                double d = LS[i] - instance.value(i);
                distance += d * d;
            }
            distance = Math.sqrt(distance);
            if (distance < EPSILON)
                return 1.0;
            return 0.0;
        } else {
            double dist = calcNormalizedDistance(instance.toDoubleArray());
            if (dist <= getRadius()) {
                return 1;
            } else {
                return 0;
            }
            // double res = AuxiliaryFunctions.distanceProbabilty(dist, LS.length);
            // return res;
        }
    }

    private double[] getVarianceVector() {
        double[] res = new double[this.LS.length];
        for (int i = 0; i < this.LS.length; i++) {
            double ls = this.LS[i];
            double ss = this.SS[i];

            double lsDivN = ls / this.getWeight();
            double lsDivNSquared = lsDivN * lsDivN;
            double ssDivN = ss / this.getWeight();
            res[i] = ssDivN - lsDivNSquared;

            // Due to numerical errors, small negative values can occur.
            // We correct this by settings them to almost zero.
            if (res[i] <= 0.0) {
                if (res[i] > -EPSILON) {
                    res[i] = MIN_VARIANCE;
                }
            } else {

            }
        }
        return res;
    }

    /**
     * Check if this cluster is empty or not.
     * 
     * @return <code>true</code> if the cluster has no data points,
     *         <code>false</code> otherwise.
     */
    public boolean isEmpty() {
        return this.N == 0;
    }

    /**
     * Calculate the normalized euclidean distance (Mahalanobis distance for
     * distribution w/o covariances) to a point.
     * 
     * @param other The point to which the distance is calculated.
     * @return The normalized distance to the cluster center.
     *
     *         TODO: check whether WEIGHTING is correctly applied to variances
     */
    // ???????
    private double calcNormalizedDistance(double[] point) {
        double[] variance = getVarianceVector();
        double[] center = getCenter();
        double res = 0.0;

        for (int i = 0; i < center.length; i++) {
            double diff = center[i] - point[i];
            res += (diff * diff);// variance[i];
        }
        return Math.sqrt(res);
    }

    /**
     * Approximates the inverse error function. Clustream needs this.
     * 
     * @param z
     */
    public static double inverseError(double x) {
        double z = Math.sqrt(Math.PI) * x;
        double res = (z) / 2;

        double z2 = z * z;
        double zProd = z * z2; // z^3
        res += (1.0 / 24) * zProd;

        zProd *= z2; // z^5
        res += (7.0 / 960) * zProd;

        zProd *= z2; // z^7
        res += (127 * zProd) / 80640;

        zProd *= z2; // z^9
        res += (4369 * zProd) / 11612160;

        zProd *= z2; // z^11
        res += (34807 * zProd) / 364953600;

        zProd *= z2; // z^13
        res += (20036983 * zProd) / 797058662400d;

        /*
         * zProd *= z2; // z^15 res += (2280356863 * zProd)/334764638208000;
         */

        // +(49020204823 pi^(17/2) x^17)/26015994740736000+(65967241200001 pi^(19/2)
        // x^19)/124564582818643968000+(15773461423793767 pi^(21/2)
        // x^21)/104634249567660933120000+O(x^22)

        return res;
    }

    @Override
    public Instance sample(Random random) {
        double[] res = new double[LS.length];
        double[] variance = getVarianceVector();
        double[] center = getCenter();
        for (int i = 0; i < res.length; i++) {
            double radius = Math.sqrt(variance[i]);
            res[i] = center[i] + random.nextGaussian() * radius;
        }

        return new DenseInstance(1.0, res);
    }

    @Override
    protected void getClusterSpecificInfo(ArrayList<String> infoTitle, ArrayList<String> infoValue) {
        super.getClusterSpecificInfo(infoTitle, infoValue);
        infoTitle.add("Deviation");

        double[] variance = getVarianceVector();
        double sumOfDeviation = 0.0;
        for (int i = 0; i < variance.length; i++) {
            double d = Math.sqrt(variance[i]);
            sumOfDeviation += d;
        }

        sumOfDeviation /= variance.length;

        infoValue.add(Double.toString(sumOfDeviation));
    }

    public double[] getLS() {
        return LS;
    }

    public double[] getSS() {
        return SS;
    }

    public String getClasse() {
        return classe;
    }
}
