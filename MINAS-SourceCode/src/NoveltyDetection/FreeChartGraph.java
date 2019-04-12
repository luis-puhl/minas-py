package NoveltyDetection;

import  org.jfree.chart.ChartFactory;
import org.jfree.chart.ChartUtilities;
import  org.jfree.chart.JFreeChart;
import org.jfree.chart.axis.NumberAxis;
import org.jfree.chart.axis.NumberTickUnit;
import org.jfree.chart.axis.ValueAxis;
import org.jfree.chart.plot.PlotOrientation;
import org.jfree.chart.plot.ValueMarker;
import org.jfree.chart.plot.XYPlot;
import org.jfree.chart.renderer.xy.XYItemRenderer;
import org.jfree.data.xy.XYDataset;
import org.jfree.data.xy.XYSeries;
import org.jfree.data.xy.XYSeriesCollection;


import java.awt.BasicStroke;
import java.awt.Color;
import java.io.*;
import java.util.List;

public class FreeChartGraph {
	   private JFreeChart graph;
	
//*********************************************************************************************
//***************************** createDataSetXY ***********************************************
//*********************************************************************************************		   	   
	   public static XYDataset createDataSetXY(List<Float> a, List<Float> b, List<Float> c, List<Float> d, int flgEvaluationType){
		   final XYSeriesCollection xyDataset = new XYSeriesCollection();
		   final XYSeries series1; 
		   final XYSeries series2; 
		   final XYSeries series3; 
		   
		   if (flgEvaluationType == 0){//Proposed Methodology
			   series1 = new XYSeries("Unk");
			   series2 = new XYSeries("FMacro");
		   }
		   else{//Methodology from the literature
			   series1 = new XYSeries("FNew");
			   series2 = new XYSeries("Mnew");
		   }
		   
		   if(a.size () != 0 && b.size () != 0 ) {

	            for(int i=0;i<a.size ();i++) {
	            	series1.add(d.get(i),a.get(i));
	            }

	            for(int i=0;i<b.size ();i++) {
	            	series2.add(d.get(i),b.get(i));
	            }
	 		   
	            if (c.size()!=0){
	            	if (flgEvaluationType == 0){
	            		series3 = new XYSeries("CER");
	            	}
	            	else {
	            		series3 = new XYSeries("Err");
	            	}
		            for(int i=0;i<c.size ();i++) {	            	
		                series3.add(d.get(i),c.get(i));
		            }
		 		   xyDataset.addSeries(series3);
	            }
		           xyDataset.addSeries(series1);
		 		   xyDataset.addSeries(series2);
	        }
		   		 		   
		   return xyDataset;
	   }
	   
//*********************************************************************************************
//***************************** addNoveltyExtensionGraph **************************************
//*********************************************************************************************			   
	   public void addNoveltyExtensionGraph(List<Integer> a, Color color, float thickness ){
		   final XYPlot plot = graph.getXYPlot();
		   ValueMarker marker;
		   for (int i=0; i< a.size();i++){
			   marker = new ValueMarker(a.get(i));
			   marker.setPaint(color);
			   marker.setStroke(new BasicStroke(thickness));
			   plot.addDomainMarker(marker);
		   }
	   }
	   
//*********************************************************************************************
//***************************** addNoveltyExtensionGraph **************************************
//*********************************************************************************************			   
	   public void createGraph( List<Float> med1, List<Float> med2, List<Float> med3, List<Float> values_Timestamp, List<Integer> values_Nov, List<Integer> values_Ext, int flagTipoAv ) throws IOException {
	    	
	        XYDataset dataXY = createDataSetXY(med1, med2, med3, values_Timestamp,flagTipoAv);        
	        graph = ChartFactory.createXYLineChart("", "Timestamp (in thousands)", "Evaluation Measure Value", dataXY, PlotOrientation.VERTICAL, true, true, false);
	        
	        addNoveltyExtensionGraph(values_Ext, Color.gray,1.0f);
	        addNoveltyExtensionGraph(values_Nov, Color.gray,1.0f);
	        	        
	        XYPlot xyplot = (XYPlot) graph.getPlot();
	        
	        ValueAxis rangeAxis = xyplot.getRangeAxis();
	        rangeAxis.setRange(0.0, 40);
	        
	        final NumberAxis rangeAxis2 = (NumberAxis) xyplot.getRangeAxis(); 
	        rangeAxis2.setTickUnit(new NumberTickUnit(10)); 

	        final NumberAxis domainAxis = (NumberAxis) xyplot.getDomainAxis(); 
	        domainAxis.setTickUnit(new NumberTickUnit(20));
	                
	        xyplot.setBackgroundPaint(Color.white);	        
	        xyplot.setDomainGridlinePaint(Color.white);
	        xyplot.setRangeGridlinePaint(Color.white);
	        
	        XYItemRenderer r = xyplot.getRenderer(); 
	        r.setSeriesStroke(0, new BasicStroke(3.0f));
	        r.setSeriesStroke(1, new BasicStroke(3.0f ));
	        r.setSeriesStroke(2, new BasicStroke(3.0f ));
	        	        
	        //record the graph in a file
	        OutputStream fileOut = new FileOutputStream("C:\\graph.png");
	        save(graph,fileOut);
	        fileOut.close();
	     }

	    
	    public void save(JFreeChart grafico, OutputStream out) throws IOException {
		     ChartUtilities.writeChartAsPNG(out, grafico, 500, 500);
		}
	    
	    public JFreeChart getGrafico(){
	    	return graph;
	    }	    
}
