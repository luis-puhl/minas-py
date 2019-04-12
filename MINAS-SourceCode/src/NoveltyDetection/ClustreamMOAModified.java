package NoveltyDetection;

import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import moa.cluster.Cluster;
import moa.cluster.Clustering;
import moa.cluster.SphereCluster;
import moa.clusterers.AbstractClusterer;
import moa.core.Measurement;
import moa.options.IntOption;
import weka.core.DenseInstance;
import weka.core.Instance;


public class ClustreamMOAModified extends AbstractClusterer{
    public IntOption timeWindowOption = new IntOption("timeWindow",
			't', "Rang of the window.", 1000);

    public IntOption maxNumKernelsOption = new IntOption(
			"maxNumKernels", 'k',
			"Maximum number of micro kernels to use.", 100);

    public static final int m = 50;
    public static final int t = 2;
    private int timeWindow;
    private long timestamp = -1;
    private ClustreamKernelMOAModified[] kernels;
    private boolean initialized;
    private List<ClustreamKernelMOAModified> buffer; // Buffer for initialization with kNN
    private int bufferSize;
    private ArrayList<ArrayList<Integer>> elemMicroClusters;    

    public ClustreamMOAModified() {
    }


    @Override
    public void resetLearningImpl() {
		this.initialized = false;
		this.timeWindow = timeWindowOption.getValue();
		this.buffer = new LinkedList<ClustreamKernelMOAModified>();	
    }

    public ArrayList<ArrayList<Integer>> getMicroClusterElements(){
    	return elemMicroClusters;
    }
    public void InicializaBufferSize(int valor){
    	this.bufferSize = valor;
    	this.kernels = new ClustreamKernelMOAModified[this.bufferSize];
    	elemMicroClusters = new ArrayList<ArrayList<Integer>>();

    }
    
    @Override
    public void trainOnInstanceImpl(Instance instance) {
        int dim = instance.numValues();
        if (timestamp==-1){
        	for (int i=0; i< this.bufferSize;i++)
    			elemMicroClusters.add(new ArrayList<Integer>());
        }
        
	timestamp++;
        // 0. Initialize
	if ( !initialized ) {
	    if ( buffer.size() < bufferSize ) {	  
		buffer.add( new ClustreamKernelMOAModified(instance,dim, timestamp) );
		return;
	    }

	    int k = kernels.length;
	    assert (k < bufferSize);

	    	    	    
	    ClustreamKernelMOAModified[] centers = new ClustreamKernelMOAModified[k];
	    for ( int i = 0; i < k; i++ ) {
		centers[i] = buffer.get( i ); // TODO: make random!
	    }
	    Clustering kmeans_clustering = kMeans(k, centers, buffer,elemMicroClusters);

	    for ( int i = 0; i < kmeans_clustering.size(); i++ ) {
		kernels[i] = new ClustreamKernelMOAModified( new DenseInstance(1.0,centers[i].getCenter()), dim, timestamp );
	    }

	    buffer.clear();
	    initialized = true;

	    //return;	    
	}


	// 1. Determine closest kernel
	ClustreamKernelMOAModified closestKernel = null;
	double minDistance = Double.MAX_VALUE;
	int kernelProximo = 0;

	for ( int i = 0; i < kernels.length; i++ ) {
	    double distance = distance(instance.toDoubleArray(), kernels[i].getCenter() );
	    if ( distance < minDistance ) {
		closestKernel = kernels[i];
		kernelProximo=i;
		minDistance = distance;
	    }
	}
	// 2. Check whether instance fits into closestKernel
	double radius = 0.0;
	if ( closestKernel.getWeight() == 1 ) {
	    // Special case: estimate radius by determining the distance to the
	    // next closest cluster
	    radius = Double.MAX_VALUE;
	    double[] center = closestKernel.getCenter();
	    for ( int i = 0; i < kernels.length; i++ ) {
		if ( kernels[i] == closestKernel ) {
		    continue;
		}

		double distance = distance(kernels[i].getCenter(), center );
		radius = Math.min( distance, radius );
	    }
	} else {
	    radius = closestKernel.getRadius();
	}

	if ( minDistance < radius ) {
	    // Date fits, put into kernel and be happy
	    closestKernel.insert( instance, timestamp );
	    elemMicroClusters.get(kernelProximo).add((int)timestamp);
            return;
	}

	// 3. Date does not fit, we need to free
	// some space to insert a new kernel
	long threshold = timestamp - timeWindow; // Kernels before this can be forgotten

	//in the offline clustream, a cluster is not forgeted
	// 3.1 Try to forget old kernels
	/*for ( int i = 0; i < kernels.length; i++ ) {
	    if ( kernels[i].getRelevanceStamp() < threshold ) {
		kernels[i] = new ClustreamKernel( instance, dim, timestamp );
		System.out.println("\n*****aqui");
		return;
	    }
	}*/

	// 3.2 Merge closest two kernels
	int closestA = 0;
	int closestB = 0;
	minDistance = Double.MAX_VALUE;
	for ( int i = 0; i < kernels.length; i++ ) {
	    double[] centerA = kernels[i].getCenter();
	    for ( int j = i + 1; j < kernels.length; j++ ) {
			double dist = distance( centerA, kernels[j].getCenter() );
			if ( dist < minDistance ) {
			    minDistance = dist;
			    closestA = i;
			    closestB = j;
			}
	    }
	}
	assert (closestA != closestB);

	kernels[closestA].add( kernels[closestB] );
	kernels[closestB] = new ClustreamKernelMOAModified( instance, dim, timestamp );
	for (int i=0;i<elemMicroClusters.get(closestB).size();i++){
		elemMicroClusters.get(closestA).add(elemMicroClusters.get(closestB).get(i));
	}
	elemMicroClusters.set(closestB,new ArrayList<Integer>());
	elemMicroClusters.get(closestB).add((int)timestamp);
		
    }

    @Override
    public Clustering getMicroClusteringResult() {
	if ( !initialized ) {
	    return new Clustering( new Cluster[0] );
	}


	ClustreamKernelMOAModified[] res = new ClustreamKernelMOAModified[kernels.length];
	for ( int i = 0; i < res.length; i++ ) {
	    res[i] = new ClustreamKernelMOAModified( kernels[i] );
	}

	return new Clustering( res );
    }

    @Override
    public boolean implementsMicroClusterer() {
        return true;
    }

    @Override
    public Clustering getClusteringResult() {
        return null;
    }

    public String getName() {
        return "Clustream " + timeWindow;
    }

    private static double distance(double[] pointA, double [] pointB){
        double distance = 0.0;
        for (int i = 0; i < pointA.length; i++) {
            double d = pointA[i] - pointB[i];
            distance += d * d;
        }
        return Math.sqrt(distance);
    }



    public static Clustering kMeans( int k, Cluster[] centers, List<? extends Cluster> data, ArrayList<ArrayList<Integer>> grupo ) {
	assert (centers.length == k);
	assert (k > 0);

	int dimensions = centers[0].getCenter().length;

	ArrayList<ArrayList<Cluster>> clustering = new ArrayList<ArrayList<Cluster>>();
	for ( int i = 0; i < k; i++ ) {
	    clustering.add( new ArrayList<Cluster>() );
	}
	
	int repetitions = 100;
	int m;
	while ( repetitions-- >= 0 ) {
	    // Assign points to clusters
		m=0;
	    for ( Cluster point : data ) {	    	
			double minDistance = distance( point.getCenter(), centers[0].getCenter() );
			int closestCluster = 0;
			for ( int i = 1; i < k; i++ ) {
			    double distance = distance( point.getCenter(), centers[i].getCenter() );
			    if ( distance < minDistance ) {
				closestCluster = i;
				minDistance = distance;
			    }
			}
	
			clustering.get( closestCluster ).add( point );
			if (repetitions == 0)
				grupo.get(closestCluster).add(m);
			m++;
	    }

	    // Calculate new centers and clear clustering lists
	    SphereCluster[] newCenters = new SphereCluster[centers.length];
	    for ( int i = 0; i < k; i++ ) {
		newCenters[i] = calculateCenter( clustering.get( i ), dimensions );
		clustering.get( i ).clear();
	    }
	    centers = newCenters;
	}
	return new Clustering( centers );
    }

    private static SphereCluster calculateCenter( ArrayList<Cluster> cluster, int dimensions ) {
	double[] res = new double[dimensions];
	for ( int i = 0; i < res.length; i++ ) {
	    res[i] = 0.0;
	}

	if ( cluster.size() == 0 ) {
	    return new SphereCluster( res, 0.0 );
	}

	for ( Cluster point : cluster ) {
            double [] center = point.getCenter();
            for (int i = 0; i < res.length; i++) {
               res[i] += center[i];
            }
	}

	// Normalize
	for ( int i = 0; i < res.length; i++ ) {
	    res[i] /= cluster.size();
	}

	// Calculate radius
	double radius = 0.0;
	for ( Cluster point : cluster ) {
	    double dist = distance( res, point.getCenter() );
	    if ( dist > radius ) {
		radius = dist;
	    }
	}
        SphereCluster sc = new SphereCluster( res, radius );
        sc.setWeight(cluster.size());
	return sc;
    }

    @Override
    protected Measurement[] getModelMeasurementsImpl() {
        throw new UnsupportedOperationException("Not supported yet.");
    }

    @Override
    public void getModelDescription(StringBuilder out, int indent) {
        throw new UnsupportedOperationException("Not supported yet.");
    }

    public boolean isRandomizable() {
        return false;
    }

    public double[] getVotesForInstance(Instance inst) {
        throw new UnsupportedOperationException("Not supported yet.");
    }


	public ArrayList<ArrayList<Integer>> getGrupo() {
		return elemMicroClusters;
	}


	
}

