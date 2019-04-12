package NoveltyDetection;

public class Cluster {

    private double meanDistance;		
	private double[] center;
	private double size;
	private double radius; 
	private String lblClasse;
    private String category;
    private int time;
    
                
    public Cluster(double meandist,double[]center, double size, double radius, String lblClasse, String cat, int time){
        	this.meanDistance = meandist;
        	this.center = center;
        	this.size = size;
        	this.radius = radius;
        	this.lblClasse = lblClasse;
        	this.category = cat;
        	this.time = time;
    }
                
        public void setMeanDistance(double meanDistance){
			this.meanDistance = meanDistance;
		}
                
        public void setCategory(String cat){
			this.category = cat;
		}
                
		public void setCenter(double[] center){
			this.center = center;
		}
		
		public void setSize(double size){
				this.size = size;
		}
 
		public void setRadius(double  radius){
				this.radius = radius;
		}
						
		public void setLblClasse(String lblClasse){
				this.lblClasse = lblClasse;
		}
                
        public double getMeanDistance(){
			return meanDistance;
		}

		public String getCategory(){
			return category;
		}
                
		public double[] getCenter(){
			return center;
		}
		
		public double getSize(){
			return size;
		}
 
		public double getRadius(){
			return radius;
		}
				
		public String getLblClasse(){
			return lblClasse;
		}

		public int getTime() {
			return time;
		}

		public void setTime(int tempo) {
			this.time = tempo;
		}
		
}	
		
		


