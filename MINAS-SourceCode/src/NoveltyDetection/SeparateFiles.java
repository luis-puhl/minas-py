package NoveltyDetection;

import java.io.*;
import java.util.*;


public class SeparateFiles {
	

/*******************************************************************************   
******************** SeparateFileOff *********************************************
********************************************************************************/  
	public ArrayList<String> SeparateFileOff(String filenameOff) throws IOException{
		BufferedReader fileOff_In = new BufferedReader(new FileReader(new File(filenameOff)));
		String line;
		ArrayList<String> classes = new ArrayList<String>();
		ArrayList<FileWriter> fileOff_Out = new ArrayList<FileWriter>();
		String at_class;
		
		//reading the offline file		
		while ((line = fileOff_In.readLine()) != null){
			String[] attributes = line.split(",");
			at_class = attributes[attributes.length-1];

			int pos = classes.indexOf(at_class);
			
			if (pos == -1){
				classes.add(at_class);
				fileOff_Out.add(new FileWriter(filenameOff+at_class));
				pos = fileOff_Out.size()-1;
			}			
			fileOff_Out.get(pos).write(line + "\n");
		}
		
		//closing files
		fileOff_In.close();
		for (int i=0; i< fileOff_Out.size(); i++)
			fileOff_Out.get(i).close();
		
		ArrayList<String> vectorClasses = new ArrayList<String> ();
		for (int i=0; i<classes.size();i++)
			vectorClasses.add(classes.get(i));
		
		return vectorClasses; 
	}		
}
