package NffvSample;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.GridLayout;
import java.awt.GridBagLayout;
import java.awt.GridBagConstraints;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.Insets;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JScrollPane;
import javax.swing.JTextField;
import javax.swing.JTextPane;
import javax.swing.JOptionPane;
import javax.swing.BorderFactory;
import javax.swing.SwingConstants;
import javax.swing.SwingUtilities;

import com.neurotechnology.Nffv.Nffv;


import com.neurotechnology.Nffv.Nffv;
import com.neurotechnology.Nffv.ScannerModule;

public class ScannerModules extends JPanel implements ActionListener {
	
	JButton load;
	JTextField database;
	JTextField password; 
	ScannerModule[] scanners;
	JCheckBox[] selections;
	
	PanelContainer owner;
	
	public ScannerModules(PanelContainer owner) {
		
		this.owner = owner;
		
		scanners = Nffv.getAvailableScannerModules();
		selections = new JCheckBox[scanners.length];
		JPanel selectionpan = new JPanel();

		selectionpan.setLayout(new GridLayout(scanners.length, 1));
		selectionpan.setPreferredSize(new Dimension(350, 23 * (scanners.length)));
		selectionpan.setMaximumSize(new Dimension(800, 23 * (scanners.length)));

		for (int i = 0; i < scanners.length; i++) {
			selections[i] = new JCheckBox(scanners[i].getName());
			selectionpan.add(selections[i]);
		}
		
		load = new JButton("Load");
		database = new JTextField();
		database.setPreferredSize(new Dimension(175, 20));
		database.setText("FingerprintDB.JavaSample.dat");
		password = new JPasswordField();
		password.setPreferredSize(new Dimension(175, 20));
		load.addActionListener(this);
		
		setLayout(new BoxLayout(this, BoxLayout.Y_AXIS));
		JPanel bottompan = new JPanel();
		GridBagLayout layout = new GridBagLayout();
		layout.columnWidths = new int[] {75, 200, 75};
		layout.rowHeights = new int[] {0, 0};
		bottompan.setLayout(layout);
		bottompan.setBorder(BorderFactory.createEmptyBorder(2, 2, 2, 2));
		
		GridBagConstraints constraints = new GridBagConstraints();
		constraints.insets = new Insets(1, 1, 1, 1);
		constraints.gridx = 0;
		constraints.gridy = 0;
		constraints.anchor = GridBagConstraints.EAST;
		bottompan.add(new JLabel("Database"), constraints);
		constraints.gridx = 1;
		constraints.gridy = 0;
		constraints.anchor = GridBagConstraints.CENTER;
		bottompan.add(database, constraints);
		constraints.gridx = 0;
		constraints.gridy = 1;
		constraints.anchor = GridBagConstraints.EAST;
		bottompan.add(new JLabel("Password", SwingConstants.RIGHT), constraints);
		constraints.gridx = 1;
		constraints.gridy = 1;
		constraints.anchor = GridBagConstraints.CENTER;
		bottompan.add(password, constraints);
		constraints.gridx = 2;
		constraints.gridy = 0;
		constraints.gridheight = 2;
		constraints.anchor = GridBagConstraints.CENTER;
		bottompan.add(load, constraints);
		bottompan.setPreferredSize(new Dimension(400, 55));
		bottompan.setMaximumSize(new Dimension(Integer.MAX_VALUE, 45));
		
		JScrollPane scrollPane = new JScrollPane(selectionpan);
		scrollPane.getVerticalScrollBar().setUnitIncrement(16);
		scrollPane.setPreferredSize(new Dimension(350, 500));
		selectionpan.setAutoscrolls(true);

		add(scrollPane);
		add(bottompan, BorderLayout.SOUTH);
		
	}

	public void actionPerformed(ActionEvent arg0) {
		
		int count = 0;
		for (JCheckBox selection : selections) 
			if (selection.isSelected()) count++;

		if (count == 0) {
			JOptionPane.showMessageDialog(null, "No scanners were selected.", "Warning", JOptionPane.WARNING_MESSAGE);
			return;
		}

		if (database.getText().length() == 0) {
			SwingUtilities.invokeLater(() -> { JOptionPane.showMessageDialog(null, "Database name cannot be empty", "IllegalArgumentException", JOptionPane.ERROR_MESSAGE); });
			return;
		}
		
		ScannerModule[] scanners = new ScannerModule[count];
		
		count = 0;
		for(int i = 0; i < selections.length; i++)
			if (selections[i].isSelected()) {
				scanners[count] = this.scanners[i];
				count++;
			}
		
		owner.setPanel(new MainPanel(scanners, database.getText(), password.getText()));
		System.out.println("Scanner modules loading done");
	}
}
