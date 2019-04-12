package NoveltyDetection;

import java.io.*;
import java.util.*;


public class Evaluation {
	ArrayList<String> offlineClassesName = new ArrayList<String>();
	ArrayList<String>problemClassesName = new ArrayList<String>();
	ArrayList <String> columnName = new ArrayList<String>();	
	
	List<Float> vectorMeasure1 = new ArrayList<Float>();
	List<Float> vectorMeasure2 = new ArrayList<Float>();
	List<Float> vectorMeasure3 = new ArrayList<Float>();
	List<Float> vectorTimestamp = new ArrayList<Float>();
	List<Integer> vectorNovelty = new ArrayList<Integer>();
	List<Integer> vectorExtension = new ArrayList<Integer>();
	
	Hashtable confusionMatrix = new Hashtable();
	int count;
	int flgEvaluationType;
		
	public Evaluation(int flg){
		flgEvaluationType = flg;
	}
	
//*********************************************************************************************
//***************************** impressaoMatrizResultados ***********************************************
//*********************************************************************************************		
	public void printConfusionMatrix(String title,FileWriter fileOut, Hashtable matrix) throws IOException{
		System.out.println("\n" +title + ": \n");
		fileOut.write("\n" + title + ": \n");
		for (int i=0; i< columnName.size(); i++){
			System.out.print("\t" + columnName.get(i));
			fileOut.write("," + columnName.get(i));
		}
		System.out.print("\n ------------------------------------------------------------------------------------------------");
		
		for (int i=0; i<matrix.size();i++){
			System.out.print("\n" + problemClassesName.get(i) );
			fileOut.write("\n" + problemClassesName.get(i));
			for (int j=0; j< ((Hashtable)matrix.get(problemClassesName.get(i))).size(); j++){
				System.out.print("\t" + ((Hashtable)matrix.get(problemClassesName.get(i))).get(columnName.get(j)));
				fileOut.write("," + ((Hashtable)matrix.get(problemClassesName.get(i))).get(columnName.get(j)));
			}
			System.out.print("\n");
		}
		System.out.println("\n\n");
		fileOut.write("\n***\n");

	}

	//*********************************************************************************************
	//***************************** incrementaMatrizConfusao ***********************************************
	//*********************************************************************************************	
	public void initializeConfusionMatrix(ArrayList<String> classesOffline)throws IOException{				
		//montando o nome das classes do conceito normal
		for (int i = 0; i<classesOffline.size();i++){
			offlineClassesName.add("C "+ classesOffline.get(i));
			problemClassesName.add(offlineClassesName.get(offlineClassesName.size()-1));
			columnName.add(offlineClassesName.get(offlineClassesName.size()-1));
		}
		Collections.sort(offlineClassesName);								
		columnName.add("Unk");
		
		//criacao do hash table de resultados com todos os valores zerados
		for (int i=0; i<problemClassesName.size();i++){
			confusionMatrix.put(problemClassesName.get(i), new Hashtable());
			for (int j=0; j<columnName.size(); j++){	
				((Hashtable)confusionMatrix.get(problemClassesName.get(i))).put(columnName.get(j), 0);
			}
		}	
		count = 0;
		
		vectorMeasure1.add(0.0f);
		vectorMeasure3.add(0.0f);		
		vectorTimestamp.add((float)(count/1000));
		
		if (flgEvaluationType !=0 )
			vectorMeasure2.add(0.0f);
		else
			vectorMeasure2.add(100.0f);
	}
//*********************************************************************************************
//***************************** addExampleConfusionMatrix *************************************
//*********************************************************************************************	
	public void addExampleConfusionMatrix(String strExClassification) throws IOException{														
		String TrueClass="", MINASClass="";						
		int value;

		//obtaining the true class and minasclass from the string containing the example classification
		String[] data = strExClassification.split("\t");
		TrueClass = "C" + data[1].split(":")[1];			
		MINASClass = data[2].split(":")[1].trim();

		//examples classified as extension of a class will computed as belonging to the class
		if (MINASClass.split(" ")[0].equals("ExtCon")){
			MINASClass = MINASClass.replace("ExtCon", "C");
		}
		//examples classified as extension of a novelty pattern will computed as belongint to the novelty pattern
		else if (MINASClass.split(" ")[0].equals("ExtNov")){
			MINASClass = MINASClass.replace("ExtNov", "N");
		}
		//if the true class of the example is a novel class, then add a line in the confusion matrix and 
		//add this class in the ProblemClasses
		if (problemClassesName.indexOf(TrueClass)==-1){
			problemClassesName.add(TrueClass); 
			confusionMatrix.put(TrueClass, new Hashtable());
			for (int j=0; j<columnName.size(); j++){	
				((Hashtable)confusionMatrix.get(TrueClass)).put(columnName.get(j), 0);
			}
		}
		value = Integer.parseInt((((Hashtable)confusionMatrix.get(TrueClass)).get(MINASClass)).toString());
		//increasing the corresponding cell in the confusion matrix
		((Hashtable)confusionMatrix.get(TrueClass)).put(MINASClass,value+1); 

		count++; //increasing the counter of examples processed
		
		//for each 1000 processed examples, compute the evaluation measures
		if (count%1000 == 0){
			//Proposed methodology
			if (flgEvaluationType ==0 ){		
				float res[] = computeMeasuresProposedMethod();
				vectorMeasure1.add(res[0]);//Unk				
				vectorMeasure2.add(res[2]);//FMacro
				vectorMeasure3.add(res[1]);//Err
				vectorTimestamp.add((float)(count/1000));
			}
			else{ // Methodology from the literature
				float res[] = computeMeasureLiteratureMethod();
				vectorMeasure1.add(res[0]);//FNew
				vectorMeasure2.add(res[1]);//MNew
				vectorMeasure3.add(res[2]);//Err
				vectorTimestamp.add((float)(count/1000));
			}
				
		}
	}
//*********************************************************************************************
//***************************** updateConfusionMatrix *****************************************
//*********************************************************************************************	
	public void updateConfusionMatrix(String info, Hashtable confusionMatrixTmp){
		String classLabel;
		if (info.contains("ThinkingNov")){
			vectorNovelty.add(count/1000); //storing the timestamps where a new novelty was detected
			String noveltyLabel = "N " + info.split(" ")[2];
			//adding a new column in the confusion matrix
			columnName.add(columnName.get(columnName.size()-1));
			columnName.set(columnName.size()-2, noveltyLabel);
			for (int i=0; i<problemClassesName.size();i++){
				((Hashtable)confusionMatrix.get(problemClassesName.get(i))).put(noveltyLabel, 0);
			}
			classLabel = noveltyLabel;			
		} 
		else{ // it is an extension
			vectorExtension.add(count/1000); //storing the timestamps where a new extension was detected
			classLabel = info.split(":")[1].split(" -")[0].trim();
		}
		
		//updating the confusion matrix, in order to remove the examples from the unknown column and put in the corresponding novelty
		Integer value, unkValue, oldValue;
		for (int i=0; i< problemClassesName.size();i++){
			if (confusionMatrixTmp.get(problemClassesName.get(i))!=null){
				value = ((Integer)confusionMatrixTmp.get(problemClassesName.get(i))).intValue();
				//remove from unknown column
				unkValue = Integer.parseInt(((Hashtable)confusionMatrix.get(problemClassesName.get(i))).get("Unk").toString());
				unkValue = unkValue - value;
				((Hashtable)confusionMatrix.get(problemClassesName.get(i))).put("Unk", unkValue);
				//putting in the correspond novelty
				oldValue = Integer.parseInt(((Hashtable)confusionMatrix.get(problemClassesName.get(i))).get(classLabel).toString());
				oldValue = oldValue + value;				
				((Hashtable)confusionMatrix.get(problemClassesName.get(i))).put(classLabel, oldValue);					
			}
		}
	}
		
//*********************************************************************************************
//***************************** printResultsGraph *********************************************
//*********************************************************************************************	
	public int printResultsGraph(String filepath)throws IOException{
		FileWriter fileConfusionMatrixOut = new FileWriter(filepath+"Matriz.csv");
		
		//***********************************************************
		// printing the final confusion matrix       
		//************************************************************
		printConfusionMatrix("Final Confusion Matrix", fileConfusionMatrixOut,confusionMatrix);

		//*****************************************************
		// calculating the final confusion matrix as a percentage confusion matrix
		//*****************************************************	
		Hashtable confusionMatrixPerc = calculateConfusionMatrixPerc();

		//*****************************************************
		// printing the final confusion matrix as a percentage confusion matrix
		//*****************************************************	
		printConfusionMatrix("Impressao em forma de porcentagem", fileConfusionMatrixOut, confusionMatrixPerc);

		fileConfusionMatrixOut.close();

		//compute the evaluation measures of the final confusion matrix 
		if (flgEvaluationType ==0 ){// Using the proposed methodology 		
			float res[] = computeMeasuresProposedMethod();
			vectorMeasure1.add(res[0]);//Unk				
			vectorMeasure2.add(res[2]);//FMacro
			vectorMeasure3.add(res[1]);//Err
			vectorTimestamp.add((float)(count/1000));
		}
		else{ // Using measures from the literature
			float res[] = computeMeasureLiteratureMethod();
			vectorMeasure1.add(res[0]);//FNew
			vectorMeasure2.add(res[1]);//MNew
			vectorMeasure3.add(res[2]);//Err
			vectorTimestamp.add((float)(count/1000));
		}
		
		//recording the evaluation measures over the stream in a file
		FileWriter f = new FileWriter(new File("C:\\measures.txt"),false);
		if (flgEvaluationType == 0)
			f.write("FMacro,Unk,CER\n");
		else
			f.write("FNew,MNew,Err\n");
		for (int i=0; i< vectorMeasure1.size(); i++){
			if (flgEvaluationType == 0)
				f.write(vectorMeasure2.get(i)+ ","+ vectorMeasure1.get(i)+ "," + vectorMeasure3.get(i));
			else
				f.write(vectorMeasure1.get(i)+ ","+ vectorMeasure2.get(i)+ "," + vectorMeasure3.get(i));
			f.write("\n");
		}
		f.close();
		
		//recording the timestamps where a novelty was detected
		FileWriter f1 = new FileWriter(new File("C:\\Novelty.txt"),false);
		f1.write("Novelty\n");
		for (int i=0; i< vectorNovelty.size(); i++){
			if (i>0){
				if (Integer.parseInt(vectorNovelty.get(i)+"")!=Integer.parseInt(vectorNovelty.get(i-1)+"")){
					f1.write(vectorNovelty.get(i)+"");			
					f1.write("\n");
				}
			}
			else{
				f1.write(vectorNovelty.get(i)+"");			
				f1.write("\n");
			}
		}
		f1.close();
		
		//recording the timestamps where an extension was detected
		FileWriter f2 = new FileWriter(new File("C:\\Extension.txt"),false);
		f2.write("Extension.txt\n");
		for (int i=0; i< vectorExtension.size(); i++){
			if (i>0){
				if (Integer.parseInt(vectorExtension.get(i)+"") != Integer.parseInt(vectorExtension.get(i-1)+"")){
					f2.write(vectorExtension.get(i)+"");			
					f2.write("\n");

				}
			}				
			else {
				f2.write(vectorExtension.get(i)+"");			
				f2.write("\n");
			}
		}
		f2.close();
						
		//generating a graph (using FreeChart) in order to show the evaluation measures over the stream
		FreeChartGraph t = new FreeChartGraph();
		t.createGraph(vectorMeasure1, vectorMeasure2, vectorMeasure3,vectorTimestamp,vectorNovelty,vectorExtension,flgEvaluationType);
		// showing the graph in a Frame
		GraphFrame frame = new GraphFrame(t.getGrafico());
		return 0;
	}
	
//***************************************************************************************************
//************************** calculateConfusionMatrixPerc ((*****************************************	
//***************************************************************************************************	
	public Hashtable calculateConfusionMatrixPerc(){	
		int lineSum = 0;
		Hashtable confusionMatrixPct = new Hashtable();
	
		for (int i=0; i<problemClassesName.size();i++){
			confusionMatrixPct.put(problemClassesName.get(i), new Hashtable());
			for (int j=0; j<columnName.size(); j++){		
				((Hashtable)confusionMatrixPct.get(problemClassesName.get(i))).put(columnName.get(j), 0);
			}
		}
		//putting each element in the matrix as a percentage
		int cellValue;
		for (int i=0; i< problemClassesName.size(); i++){
			lineSum = 0;
			for (int j=0; j< columnName.size(); j++){
				lineSum += Integer.parseInt(((Hashtable)confusionMatrix.get(problemClassesName.get(i))).get(columnName.get(j)).toString());
			}
			for (int j=0; j< columnName.size(); j++){
				cellValue = Integer.parseInt(((Hashtable)confusionMatrix.get(problemClassesName.get(i))).get(columnName.get(j)).toString());
				((Hashtable)confusionMatrixPct.get(problemClassesName.get(i))).put(columnName.get(j),(double)cellValue/lineSum);
			}
		}
		return confusionMatrixPct;
	}

//***************************************************************************************************
//**************************ExibeResultadosFolds*****************************************************	
//***************************************************************************************************	
		/*public int ExibeResultadosFolds(String nomeArquivo) throws IOException{
			int nroLinhas = ((Hashtable)MatrizesConfusaoPorcFolds.get(0)).size();
			ArrayList <String> nomeColuna = new ArrayList<String>();
			
			//cada fold pode produzir tabelas com diferente nro de colunas (algumas folds encontram +/- novidades q outras)
			// encontrar o maior nro de colunas
			int nroColunas = 0;
			for (int i=0; i< MatrizesConfusaoPorcFolds.size(); i++){
				if (((Hashtable)((Hashtable)MatrizesConfusaoPorcFolds.get(i)).get(problemClassesName.get(0))).size() > nroColunas)
					nroColunas = ((Hashtable)((Hashtable)MatrizesConfusaoPorcFolds.get(i)).get(problemClassesName.get(0))).size();
			}
			
			double soma; 
			FileWriter arquivoSaida = new FileWriter(nomeArquivo);
			
			//impressao dos titulos
			for (int j=0; j<offlineClassesName.size(); j++){
				arquivoSaida.write("," + offlineClassesName.get(j));
				nomeColuna.add(offlineClassesName.get(j));
			}
			int nroNov = nroColunas - offlineClassesName.size() -1;
			for (int j=0; j<nroNov; j++){
				arquivoSaida.write("," + "N " + (j+1));
				nomeColuna.add("N " + (j+1));
			}
			arquivoSaida.write ("," + "nao sei");
			nomeColuna.add("não sei");
			
			//calculo da media das n-folds
			for (int i=0; i< nroLinhas; i++){
				arquivoSaida.write("\n" + problemClassesName.get(i));
				for (int j=0; j<nroColunas; j++){
					soma = 0;
					for (int k=0; k<MatrizesConfusaoPorcFolds.size(); k++){
						if (((Hashtable)((Hashtable)MatrizesConfusaoPorcFolds.get(k)).get(problemClassesName.get(i))).containsKey(nomeColuna.get(j)))
							soma = soma + Double.parseDouble(((Hashtable)((Hashtable)MatrizesConfusaoPorcFolds.get(k)).get(problemClassesName.get(i))).get(nomeColuna.get(j)).toString()); 
						else
							soma+=0;
					}
					arquivoSaida.write("," + (double)soma/MatrizesConfusaoPorcFolds.size());
				}
			}
			arquivoSaida.close();
			return 0;
		}*/
		
//***************************************************************************************************
//**************************** computeMeasuresProposedMethod ****************************************
//***************************************************************************************************
	public float[] computeMeasuresProposedMethod(){
		float combinedErrPerClass[],unknownRatePerClass[];
		int numTotExamplePerClassNoUnk[], numUnkPerClass[],numTotExamplePerClass[];
		int numFalsePositivePerClass[],numFalseNegativePerClass[],numTruePositivePerClass[], numTrueNegativePerClass[];
		float combinedErr,unkownRate=0,meanUnk;
		int cell,numTotalUnk=0,numTotalExamples=0;
		
		int numProblemClasses = problemClassesName.size();
		combinedErrPerClass = new float[numProblemClasses];
		numTotExamplePerClassNoUnk = new int[numProblemClasses];
		numUnkPerClass = new int[numProblemClasses];
		numFalsePositivePerClass = new int[numProblemClasses];
		numFalseNegativePerClass = new int[numProblemClasses];
		numTruePositivePerClass = new int[numProblemClasses];
		numTrueNegativePerClass = new int[numProblemClasses];
		numTotExamplePerClass = new int[numProblemClasses];
		unknownRatePerClass = new float[numProblemClasses];
		
		//computing measures relative to the Unknowns
		for (int i=0; i<numProblemClasses; i++){
			for (int j=0;j<columnName.size(); j++){
				cell = Integer.parseInt(((Hashtable)confusionMatrix.get(problemClassesName.get(i))).get(columnName.get(j)).toString());
				if (j== (columnName.size()-1)){
					numUnkPerClass[i] = cell;
				}
				numTotExamplePerClass[i] = numTotExamplePerClass[i] + cell;
			}
			
			numTotExamplePerClassNoUnk[i] = numTotExamplePerClass[i] - numUnkPerClass[i];
			numTotalUnk = numTotalUnk + numUnkPerClass[i];
			numTotalExamples = numTotalExamples + numTotExamplePerClass[i];
			if (numTotExamplePerClass[i] == 0){
				unknownRatePerClass[i] =0;
			}
			else
				unknownRatePerClass[i] = (float)numUnkPerClass[i]/numTotExamplePerClass[i];
			unkownRate = unkownRate + unknownRatePerClass[i];
		}
		meanUnk = (float)numTotalUnk/numTotalExamples;
		unkownRate = unkownRate/problemClassesName.size();
		
		//computing FP and FN
		ArrayList<Integer>[] vetCorrespCProbCMinas = computeCorrespondeProblemClassNovMINAS();
		computeFPFN(vetCorrespCProbCMinas,numTruePositivePerClass,numFalsePositivePerClass,numFalseNegativePerClass);

		//computing FMeasure
		float resFMeasure[] = computeFMeasure(numTruePositivePerClass, numFalsePositivePerClass, numFalseNegativePerClass);
		float FMeasureMacro = resFMeasure[1]*100;
				
		//compute TN
		int numTotalExampleNoUnk=0;
		for (int e=0;e<numTrueNegativePerClass.length;e++){
			numTotalExampleNoUnk = numTotalExampleNoUnk + numTotExamplePerClassNoUnk[e];
		}
		for (int e=0;e<numTrueNegativePerClass.length;e++){
			numTrueNegativePerClass[e] = numTotalExampleNoUnk-(numTruePositivePerClass[e]+ numFalseNegativePerClass[e]+numFalsePositivePerClass[e]);
		}

		//computing the combined error
		float falsePositiveRate, falseNegativeRate,sumCombinedErr=0;
		for (int e=0; e<combinedErrPerClass.length;e++){
			if ((numFalsePositivePerClass[e]+numTrueNegativePerClass[e])!=0)
				falsePositiveRate = (float)numFalsePositivePerClass[e]/(numFalsePositivePerClass[e]+numTrueNegativePerClass[e]);
			else
				falsePositiveRate = 0;
			if ((numFalseNegativePerClass[e]+numTruePositivePerClass[e])!=0)
				falseNegativeRate = (float)numFalseNegativePerClass[e]/(numFalseNegativePerClass[e]+numTruePositivePerClass[e]);
			else
				falseNegativeRate = 0;
			combinedErrPerClass[e] = numTotExamplePerClassNoUnk[e]*(falsePositiveRate + falseNegativeRate);
			sumCombinedErr = sumCombinedErr + combinedErrPerClass[e];
		}
		if (numTotalExampleNoUnk == 0)
			combinedErr = 0.0f;
		else combinedErr = sumCombinedErr/(2*numTotalExampleNoUnk);

		float evaluationMeasures[] = new float [3];
		evaluationMeasures[0] = unkownRate*100;   
		evaluationMeasures[1] = combinedErr*100; 
		evaluationMeasures[2] = FMeasureMacro;
		return evaluationMeasures;
	}
	
//***************************************************************************************************
//**************************** calculaMedidaAvaliacao2********************************************
//***************************************************************************************************
	public float[] computeMeasureLiteratureMethod(){
		int FpPerClass[], FnPerClass[], unknownPerClass[], FePerClass[];		
		int i, cell;
		int numTotalExPerClass[]; 	
				
		//initializing vectors
		int nroClassesProb = problemClassesName.size();
		FpPerClass = new int[offlineClassesName.size()];
		FePerClass = new int[offlineClassesName.size()];
		FnPerClass = new int[nroClassesProb-offlineClassesName.size()];
		unknownPerClass = new int[nroClassesProb];
		numTotalExPerClass = new int[nroClassesProb];

		//computing hits and err in the known classes
		for (i=0; i<offlineClassesName.size(); i++){
			for (int j=0;j<((Hashtable)confusionMatrix.get(offlineClassesName.get(i))).size(); j++){
				cell = Integer.parseInt(((Hashtable)confusionMatrix.get(offlineClassesName.get(i))).get(columnName.get(j)).toString());
				numTotalExPerClass[i] = numTotalExPerClass[i] + cell;
				if (j <offlineClassesName.size()){
					if (i!=j)
						FePerClass[i] = FePerClass[i] + cell; 
				}
				else if (j== (columnName.size()-1)){
					unknownPerClass[i] = cell;
				}
				else {
					FpPerClass[i] = FpPerClass[i] + cell;
				}
			}
		}
		
		//computing hits and errors in the novel classes
		for(int k=i;k<nroClassesProb;k++){
			for (int j=0;j<columnName.size(); j++){
				cell = Integer.parseInt(((Hashtable)confusionMatrix.get(problemClassesName.get(k))).get(columnName.get(j)).toString());
				numTotalExPerClass[k] = numTotalExPerClass[k] + cell;
				if (j<offlineClassesName.size())
					FnPerClass[k-i] = FnPerClass[k-i] + cell;
				else if (j == (columnName.size()-1))
					unknownPerClass[k] = cell;
			}
		}
		
		//computing Mnew (Fn*100/Nc)  Fnew ((Fp*100)/(N-Nc) e Err((Fp + Fn +Fe)*100/N)
		//FNew
		float FNew, Fp = 0, NroExCNormal=0, Fe = 0; // (N - Nc) 
		for (i=0; i<offlineClassesName.size(); i++){
			Fp = Fp + FpPerClass[i] + unknownPerClass[i];
			NroExCNormal = NroExCNormal + numTotalExPerClass[i];			
			Fe = Fe + FePerClass[i];
		}
		if (NroExCNormal == 0)
			FNew = 0.0f;
		else FNew = (float)(Fp*100) /NroExCNormal;
		
		//Mnew
		float MNew=0, Fn=0, NroExNov=0;
		for (i=offlineClassesName.size(); i<nroClassesProb; i++){
			Fn = Fn + FnPerClass[i-offlineClassesName.size()];
			NroExNov = NroExNov + numTotalExPerClass[i];
		}	
		if (NroExNov == 0.0)
			MNew = 0.0f;
		else MNew = (float)(Fn*100) / NroExNov;
		
		
		//Err 
		float Err;		
		Err = (float)((Fp + Fn + Fe)*100)/(NroExCNormal+NroExNov);
		
		
		float evaluationaMeasures[] = new float [3];
		evaluationaMeasures[0] = FNew;       
		evaluationaMeasures[1] = MNew; 
		evaluationaMeasures[2] = Err;
		return evaluationaMeasures;
	}

//***************************************************************************************************
//**************************** calcularCorrespondCMinasCProb ****************************************
//***************************************************************************************************
	public ArrayList<Integer>[] computeCorrespondeProblemClassNovMINAS(){
		int max=0; int maxPos=0;
		int cell;
		ArrayList<Integer>[] vectorCorrespondeProblemClasNovMINAS= new ArrayList[problemClassesName.size()];

		for (int i=0; i<vectorCorrespondeProblemClasNovMINAS.length;i++)
			vectorCorrespondeProblemClasNovMINAS[i] = new ArrayList<Integer>();
		
		//for the offline classes, the correspondence is direct
		for (int i=0; i<offlineClassesName.size();i++){
			vectorCorrespondeProblemClasNovMINAS[i].add(i);
		}
		
		//for each novelty, to find the corresponding class, based on the number of classified examples
		for (int i=offlineClassesName.size(); i<columnName.size()-1;i++){
			max = 0; maxPos = 0;
			for (int j=0;j<problemClassesName.size();j++){
				cell = Integer.parseInt(((Hashtable)confusionMatrix.get(problemClassesName.get(j))).get(columnName.get(i)).toString());
				if (cell > max){
					max = cell;
					maxPos = j;
				}
			}
			vectorCorrespondeProblemClasNovMINAS[maxPos].add(i);
		}

		return vectorCorrespondeProblemClasNovMINAS;
	}
//**********************************************************************************************
//************************* computeFPFN *******************************************************
//**********************************************************************************************	
	public void computeFPFN(ArrayList<Integer>[] vetorCorrespondenceCProbNovMINAS,int numTruePositivePerClass[], int numFalsePositivePerClass[], int numFalseNegativePerClass[]){
		int cell,pos;
		
		//computing TP and FN
		for (int i=0;i<problemClassesName.size();i++){
			for (int j=0;j<columnName.size()-1;j++){
				cell = Integer.parseInt(((Hashtable)confusionMatrix.get(problemClassesName.get(i))).get(columnName.get(j)).toString());
				//if there is a correspondence between the column and the class 
				if (belong(j,vetorCorrespondenceCProbNovMINAS[i])== 1)
					numTruePositivePerClass[i] = numTruePositivePerClass[i]+cell;
				else
					numFalseNegativePerClass[i] = numFalseNegativePerClass[i]+cell;
			}
		}
		
		//computing FP 
		for(int j=0;j<columnName.size()-1;j++){
			pos = search(j,vetorCorrespondenceCProbNovMINAS);
			for (int i=0;i<problemClassesName.size();i++){
				cell = Integer.parseInt(((Hashtable)confusionMatrix.get(problemClassesName.get(i))).get(columnName.get(j)).toString());
				if (i != pos){
					numFalsePositivePerClass[pos] = numFalsePositivePerClass[pos] + cell;
				}
			}
		}				
	}
//**********************************************************************************************
//****************************** belong ******************************************************	
//**********************************************************************************************	
	public int belong (int elem, ArrayList<Integer> vet){
		for (int i=0; i<vet.size();i++)
			if (elem == (Integer)vet.get(i))
				return 1;
		return 0;
	}
//**********************************************************************************************
//******************************* procura ******************************************************	
//**********************************************************************************************	
	public int search(int elem, ArrayList<Integer> vector[]){
		for (int i=0; i<vector.length; i++){
			for (int j=0; j<vector[i].size(); j++)
				if ((Integer)vector[i].get(j) == elem)
					return i;
		}
		return 0;
	}
//**********************************************************************************************
//****************************** calculaFMeasure ***********************************************
//**********************************************************************************************	
	public float[] computeFMeasure(int numTruePositivePerClass[], int numFalsePositivePerClass[], int numFalseNegativePerClass[]){		
		float pi, ro;
		int i,numerator=0, denominatorPredict=0, denominatorTrue=0;
		float FMeasurePorClasse[];
		float FMeasureMicro=0, FMeasureMacro=0;
		FMeasurePorClasse = new float[problemClassesName.size()];

		int numClasses = 0;
		//computing f-measure micro
		for (i=0; i<problemClassesName.size();i++){
				numerator = numerator + numTruePositivePerClass[i];
				denominatorPredict = denominatorPredict + (numTruePositivePerClass[i] + numFalsePositivePerClass[i]);
				denominatorTrue = denominatorTrue + (numTruePositivePerClass[i] + numFalseNegativePerClass[i]);
		}
		pi = (float)numerator/denominatorPredict;
		ro = (float)numerator/denominatorTrue;
		FMeasureMicro = (float)(2*pi*ro)/(pi+ro);
		
		//computing FMeasureMacro
		for (i=0;i<problemClassesName.size();i++){
			if (numTruePositivePerClass[i]+numFalseNegativePerClass[i] > 0){ 
				if (numTruePositivePerClass[i]+numFalsePositivePerClass[i] == 0)
					pi = 0.0f;
				else pi = (float)numTruePositivePerClass[i]/(numTruePositivePerClass[i]+numFalsePositivePerClass[i]);
				ro = (float)numTruePositivePerClass[i]/(numTruePositivePerClass[i]+numFalseNegativePerClass[i]);
				if ((pi+ro) == 0)
					FMeasurePorClasse[i] = 0.0f;
				else FMeasurePorClasse[i] = (float)(2*pi*ro)/(pi+ro);
				FMeasureMacro = FMeasureMacro + FMeasurePorClasse[i];
				numClasses++;
			}
		}
		FMeasureMacro = FMeasureMacro/numClasses;
		float res[] = new float[2];
		res[0] = FMeasureMicro;
		res[1] = FMeasureMacro;
		return res;
	}
}
