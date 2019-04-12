package NoveltyDetection;

import javax.swing.*;
import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;

public class GraphFrame extends JFrame{

	private static final long serialVersionUID = 1L;

	public GraphFrame(JFreeChart grafico){
		super("Graphic - Evaluation Measures");
		ChartPanel chartPanel = new ChartPanel(grafico);
        //chartPanel.setPreferredSize(new java.awt.Dimension(500, 270));
        setContentPane(chartPanel);
		setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		setSize(500,300);
		setVisible(true);
	}
}
