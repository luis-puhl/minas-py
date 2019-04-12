package NoveltyDetection;

import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.beans.EventHandler;
import java.io.File;
import java.io.IOException;

import javax.swing.*;

public class MINASFrame extends JFrame{
	private Container c;
    private JPanel panel;
    private JButton btnExecute;
    private JButton btnFileOn;
    private JButton btnFileOff;
    private JButton btnFileOut;    
    private JButton btnCancelar;
    private JTextField txtOfflineFile;
    private JTextField txtOnlineFile;
    private JTextField txtOutDirectory;
    private JComboBox cbxAlgOffline;
    private JComboBox cbxAlgOnline;
	private JComboBox cbxEvaluation; 
	private JTextField txtNumClusters;
	private JTextField txtThresholdNovelty;
	private JTextField txtForgettingPast; 
    
	public MINASFrame (){   
		createContainer();
        this.repaint();
        this.show();
    }

	public void createContainer() {
	    FlowLayout layout;
	    
		c = getContentPane(); 
        layout = new FlowLayout();        
        panel = new JPanel();
		//handler = new EventHandler();
		
        //********File Offline
		JLabel lblOfflineFile = new JLabel();
		lblOfflineFile.setText("Offline File (training): ");
		panel.add(lblOfflineFile);
		
		txtOfflineFile = new JTextField();
		txtOfflineFile.setPreferredSize(new Dimension(200,20));
		panel.add(txtOfflineFile);
		
		btnFileOff = new JButton();
		btnFileOff.setText("...");
		buttonOpenOffEvent hOpenOff = new buttonOpenOffEvent();
        btnFileOff.addActionListener(hOpenOff);
		panel.add(btnFileOff);		
		
        //********File Online
		JLabel lblOnlineFile = new JLabel();
		lblOnlineFile.setText("Online File (stream): ");
		panel.add(lblOnlineFile);
		
		txtOnlineFile = new JTextField();
		txtOnlineFile.setPreferredSize(new Dimension(200,20));
		panel.add(txtOnlineFile);
		
		btnFileOn = new JButton();
		btnFileOn.setText("...");
		buttonOpenOnEvent hOpenOn = new buttonOpenOnEvent();
        btnFileOn.addActionListener(hOpenOn);
		panel.add(btnFileOn);		

		
		//********Output Directory
		JLabel lblOutDirectory = new JLabel();
		lblOutDirectory.setText("Output Filename: ");
		panel.add(lblOutDirectory);
				
		txtOutDirectory = new JTextField();
		txtOutDirectory.setPreferredSize(new Dimension(250,20));
		panel.add(txtOutDirectory);
		
		btnFileOut = new JButton();
		btnFileOut.setText("...");
		buttonOpenOutEvent hOpenOut = new buttonOpenOutEvent();
        btnFileOut.addActionListener(hOpenOut);
		panel.add(btnFileOut);	
		
		//******************Alg Offline
		JLabel lblAlgOfflinePhase = new JLabel();
		lblAlgOfflinePhase.setText("Algorithm for the offline phase: ");
		panel.add(lblAlgOfflinePhase);
		
		String algOffline[] = {"clustream", "kmeans","clustream+kMeans"};
		cbxAlgOffline = new JComboBox(algOffline);
		panel.add(cbxAlgOffline);
		
		//*********************Alg Online
		JLabel lblAlgOnlinePhase = new JLabel();
		lblAlgOnlinePhase.setText("Algorithm for the online phase: ");
		panel.add(lblAlgOnlinePhase);
		
		String algOnline[] = {"clustream", "Kmeans"};
		cbxAlgOnline = new JComboBox(algOnline);
		cbxAlgOnline.setPreferredSize(new Dimension(150,20));
		panel.add(cbxAlgOnline);
		
		//********************* Number of Clusters
		JLabel lblNumClusters = new JLabel();
		lblNumClusters.setText("Number of micro-clusters: ");
		panel.add(lblNumClusters);
		
		txtNumClusters = new JTextField();
		txtNumClusters.setPreferredSize(new Dimension(200,20));
		txtNumClusters.setText("100");
		panel.add(txtNumClusters);
		
		//********************* Threshold		
		JLabel lblThreshold = new JLabel();
		lblThreshold.setText("Threshold for novelty detection: ");
		panel.add(lblThreshold);
		
		txtThresholdNovelty = new JTextField();
		txtThresholdNovelty.setPreferredSize(new Dimension(200,20));
		txtThresholdNovelty.setText("2.0");
		panel.add(txtThresholdNovelty);
		
		//********************* Forgetting Factor	
		JLabel lblForgettingFactor = new JLabel();
		lblForgettingFactor.setText("Threshold for forgetting the past: ");
		panel.add(lblForgettingFactor);
		
		txtForgettingPast = new JTextField();
		txtForgettingPast.setPreferredSize(new Dimension(200,20));
		txtForgettingPast.setText("10000");
		panel.add(txtForgettingPast);
		
		//********************* Evaluation
		JLabel lblTypeEvaluation = new JLabel();
		lblTypeEvaluation.setText("Methodology Type for Evaluation: ");
		panel.add(lblTypeEvaluation);
		
		String evaluation[] = {"Proposed Methodology","Literature Methodology"};
		cbxEvaluation = new JComboBox(evaluation);
		cbxEvaluation.setPreferredSize(new Dimension(200,20));
		panel.add(cbxEvaluation);
		
		//********************* Buttons
		btnExecute = new JButton();
        btnExecute.setText("Execute");
		buttonExecutionEvent hExec = new buttonExecutionEvent();
        btnExecute.addActionListener(hExec);
        panel.add(btnExecute);
                
        btnCancelar = new JButton();
        btnCancelar.setText("Cancelar");
        buttonCloseEvent hClose = new buttonCloseEvent();
        btnCancelar.addActionListener(hClose);
        panel.add(btnCancelar);
                        
        c.add(panel);       
        this.setLocation(50,50);
        this.setSize(new Dimension(450,400));	
        this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
	}
	public void executeMINAS() throws IOException, NumberFormatException{
		String algOff, algOn, outDirectory, filenameOff,filenameOnl;
		double thr;
		int forg, numC;
		boolean flagMicro;
		if (cbxAlgOffline.getSelectedItem().toString().equals("clustream+kMeans")==true){
			algOff = "clustream";
			flagMicro = false;
		}
		else{
			algOff = cbxAlgOffline.getSelectedItem().toString();
			flagMicro = true;
		}
		algOn =cbxAlgOnline.getSelectedItem().toString();
		thr = Double.parseDouble(txtThresholdNovelty.getText()); 
		forg = Integer.parseInt(txtForgettingPast.getText());
		numC = Integer.parseInt(txtNumClusters.getText()); 
		outDirectory = txtOutDirectory.getText();
		filenameOff = txtOfflineFile.getText();
		filenameOnl = txtOnlineFile.getText();
		MINAS m = new MINAS(filenameOff, filenameOnl,outDirectory, algOff,algOn ,thr, cbxEvaluation.getSelectedIndex(), forg, numC, flagMicro);
    	m.execution();		
	}
	
	//class for button event treatment
	class buttonExecutionEvent implements ActionListener{	
		@Override
		public void actionPerformed(ActionEvent arg0) {
			// TODO Auto-generated method stub		
			try {
				executeMINAS();
			} catch (NumberFormatException | IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}
	}
	
	class buttonOpenOffEvent implements ActionListener{
		@Override
		public void actionPerformed(ActionEvent e) {
			// TODO Auto-generated method stub
			String filepath = openFile(1);
			txtOfflineFile.setText(filepath);
		}		
	}
	class buttonOpenOnEvent implements ActionListener{
		@Override
		public void actionPerformed(ActionEvent e) {
			// TODO Auto-generated method stub
			String filepath = openFile(1);
			txtOnlineFile.setText(filepath);
		}	
	}
	class buttonOpenOutEvent implements ActionListener{
		@Override
		public void actionPerformed(ActionEvent e) {
			// TODO Auto-generated method stub
			String filepath = openFile(0);
			txtOutDirectory.setText(filepath);
			
		}		
	}
	class buttonCloseEvent implements ActionListener{
		@Override
		public void actionPerformed(ActionEvent e) {
			// TODO Auto-generated method stub
			close();
		}
	}
	
	private String openFile(int flg){
		JFileChooser OpenFrame = new JFileChooser();
		File file = new File("");
		String filepath = "";
	
		OpenFrame.setDialogTitle("Open File");
		if (flg == 0)
			OpenFrame.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
		else
			OpenFrame.setFileSelectionMode(JFileChooser.FILES_ONLY);
		//OpenFrame.setCurrentDirectory(new File("C:\\Users\\Elaine\\Documents\\"));
		int result = OpenFrame.showOpenDialog(this);
		if (result == JFileChooser.APPROVE_OPTION) {
			file = OpenFrame.getSelectedFile();
			filepath = file.getPath();
		}
		return filepath;
	}
	
	private void close(){
		this.dispose();
	}
	public static void main(String args[]){
		MINASFrame f = new MINASFrame();
	}
}
