package NoveltyDetection;
import java.io.*;
import java.util.ArrayList;
import moa.cluster.Clustering;
import weka.core.DenseInstance;
import weka.core.Instance;


public class ClustreamOffline {
   	private Clustering microClusters;
    Clustering resultingClusters; //can be micro or macro clusters
    private boolean flagMicro;
	private int numResultingClusters;
	private double[] clusterSize;
	private String classLabel;	//label of the class to which will be modeled a set of clusters to represent it
    private int clusterExample[]; //vector of size: number of examples. Each position contains the number of the cluster in which the example was classified    
    ArrayList<ArrayList<Integer>> elemMacroCluster= new ArrayList<ArrayList<Integer>>();	   	
	private double meanDistance[]; 

/*******************************************************************************   
******************** CluStreamOff *************************************************
********************************************************************************/   
	public ArrayList<double[]> CluStreamOff(String classLabel, String filepath, float nMicro,boolean flagMicro) throws IOException{	
		this.classLabel = classLabel;
        this.flagMicro = flagMicro;
   		microClusters = null;
        
		BufferedReader fileIn = null;	        
        String line;   		   		
   		Clustering macroClusters = null;

   		ClustreamMOAModified algClustream = new ClustreamMOAModified();
    	algClustream.prepareForUse();
    	algClustream.InicializaBufferSize((int)nMicro);    	
    		
    	//reading the datafile and creating the set of clusters 
    	int size=0;
        fileIn = new BufferedReader(new FileReader(new File(filepath+classLabel)));
        double fileLine[]=null;
   		while ((line = fileIn.readLine()) != null){			
   			String fileLineString []= line.split(",");
   			size = fileLineString.length-1;
   			fileLine = new double[size];
   			for (int i=0; i<size; i++){
   				fileLine[i] = Double.parseDouble(fileLineString[i]);
   	        } 	        
   			Instance inst= new DenseInstance(1, fileLine);	
   			algClustream.trainOnInstanceImpl(inst);				
   		}
   		fileIn.close();
   		
   		//get the resulting microclusters  
       	microClusters = algClustream.getMicroClusteringResult();
       	
        //vector containing for each micro-cluster their elements
       	ArrayList<ArrayList<Integer>> elemMicroCluster = new ArrayList<ArrayList<Integer>>(); 
       	elemMicroCluster = algClustream.getMicroClusterElements();
       		
       	ArrayList<double[]> centers = new ArrayList<double[]>();   
       	
       	//********************if the microclusters have to be macroclustered using the KMeans
       	if (flagMicro == false){   
       		       				
       		//choose the best value for K and do the macroclustering using KMeans
       		macroClusters = KMeansMOAModified.OMRk(microClusters,0,elemMacroCluster);        
       		numResultingClusters = macroClusters.size();      
       		resultingClusters = macroClusters;
       		
           	
          //vector containing for each macro-clusters the elements in this cluster
            ArrayList<Integer> finalMacroClustering[];            	
           	finalMacroClustering = (ArrayList<Integer>[])new ArrayList[numResultingClusters];           	
           	for (int i=0; i<finalMacroClustering.length;i++){
    			finalMacroClustering[i] = new ArrayList<Integer>();
    		}
           	
           	//keep a vector of size: numberofMacroClusters
           	//each position keeps a vector with all elements that belongs to this clusters
    		for (int i=0; i<elemMacroCluster.size();i++){
    			for (int j=0; j<elemMacroCluster.get(i).size();j++){
    				int pos = elemMacroCluster.get(i).get(j);
    				for (int k=0; k< elemMicroCluster.get(pos).size();k++){
    					finalMacroClustering[i].add((int)elemMicroCluster.get(pos).get(k));
    				}
    			}
    		}
    		
    		clusterExample = getFinalMacroClustering(finalMacroClustering);
    		    		
    		//number of elements in each macro-clusters
           	clusterSize=new double[(int)macroClusters.size()];
       		for (int k= 0; k<numResultingClusters; k++){
    			centers.add(macroClusters.getClustering().get(k).getCenter());
    			clusterSize[k]= elemMacroCluster.get(k).size();
    		}       		
       	}
       	
       	//else: using the micro-clusters without macro-clustering
       	else{ 
       		resultingClusters = microClusters;
           	           	
    		int nroelem = 0;
    		for (int i=0; i<elemMicroCluster.size();i++){
    			nroelem += elemMicroCluster.get(i).size();
    		}
    		clusterExample = new int[nroelem];
    		int value;
    		//to keep a vector of size: number of elements. Each position contains the number of the cluster of the corresponding element
    		for (int i=0; i<elemMicroCluster.size();i++){
    			//if the micro-cluster has less than 3 elements, then discard it
    			if (((ClustreamKernelMOAModified)microClusters.get(i)).getWeight() < 3)
    				value = -1;
    			else 
    				value = i;
    			
    			for (int j=0;j<elemMicroCluster.get(i).size();j++){
    				clusterExample[elemMicroCluster.get(i).get(j)] = value; 
    			}
    			if (((ClustreamKernelMOAModified)microClusters.get(i)).getWeight() < 3){
    				microClusters.remove(i);
    				elemMicroCluster.remove(i);
    				i--;
    			}
    		}
       		numResultingClusters = (int)microClusters.size();
           	clusterSize= new double[numResultingClusters];
 
       		for (int k= 0; k<numResultingClusters; k++){
    			centers.add(microClusters.getClustering().get(k).getCenter());
    			clusterSize[k]= elemMicroCluster.get(k).size();    			
    		}
       	}       	              
       	return centers;       	       	       	
	}

	public double[] getClusterSize(){
		return clusterSize;
	}
/*******************************************************************************   
******************** getRadius *************************************************
********************************************************************************/   	
	//get the radius or the maximum distance between an element to its centroid
	//in the clustream it is not possible to obtain this, but it is possible to obtain the radius that is the mean distance between elements and centroid *2 
	public double[] getRadius(){
		double []radius = new double[numResultingClusters];
		meanDistance = new double[numResultingClusters];
		
		if (flagMicro==false){ //in this case it was used clustream + kmeans (macro-clustering in the micro-clusters)
			double [] centeres;
			double maxDistance;
			double [] elem;
			double sum, distance;
			
			for (int i=0; i<numResultingClusters;i++){ // for each macro-clustering
				centeres = resultingClusters.get(i).getCenter(); //obtaining the center of the macro-clusters
				maxDistance = 0;
				for (int j=0;j<elemMacroCluster.get(i).size(); j++){ //para cada elemento no macro-cluster
					elem = microClusters.get(elemMacroCluster.get(i).get(j)).getCenter();
					sum=0;
		   			for (int l=0; l< elem.length; l++){ //distancia do elem ao centro
		   				sum = sum + Math.pow(centeres[l] - elem[l], 2);
		   			}
		   			distance = Math.sqrt(sum);
		   			meanDistance[i] = meanDistance[i]+distance;
		   			if (distance > maxDistance) 
		   				maxDistance = distance;
				}
		   		radius[i] = maxDistance;
		   		//another option is to obtain the radius of the macro-clustering
		   		radius[i] =  ((ClustreamKernelMOAModified)resultingClusters.get(i)).getRadius();
			}
		}
		else{//in this case only the micro-clusters will be used 
			for (int i=0; i<numResultingClusters;i++){
				radius[i] = ((ClustreamKernelMOAModified)resultingClusters.get(i)).getRadius();
				meanDistance[i] = ((ClustreamKernelMOAModified)resultingClusters.get(i)).getRadius()/2;
			}
		}
		return radius;
	}
/*******************************************************************************   
******************** meanDistance *******************************************
********************************************************************************/   	
	public double[] meanDistance(){
		double res[] = new double[numResultingClusters];
		for (int i=0; i<numResultingClusters;i++){
			if (flagMicro==false)
				res[i]= meanDistance[i]/clusterSize[i];
			else
				res[i]= meanDistance[i];
		}
		return res;
	}
/*******************************************************************************   
******************** getClusterClass *******************************************
********************************************************************************/   	
	public String[] getClusterClass(){
		String vetClusterClass [] = new String[numResultingClusters];
		for (int i=0; i<numResultingClusters; i++)
			vetClusterClass[i] = classLabel;
		return vetClusterClass;
	}
	
	public int [] getClusterExample(){
			return clusterExample;			
	}

/*******************************************************************************   
******************** getFinalMacroClustering ***********************************
********************************************************************************/    
	public int[] getFinalMacroClustering(ArrayList<Integer> finalMacroClustering[]){
		int result[];
		int numberofElements = 0;
		for (int i=0; i<finalMacroClustering.length;i++){
			numberofElements += finalMacroClustering[i].size();
		}
		result = new int[numberofElements];
		
		for (int i=0; i<finalMacroClustering.length;i++){
			for (int j=0;j<finalMacroClustering[i].size();j++){
				result[finalMacroClustering[i].get(j)] = i+1;
			}
		}
		return result;
	}

}

