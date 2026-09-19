using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;

using Neurotec.Biometrics;

namespace CSharpSample
{
	public partial class ChooseScannerForm : Form
	{
		private string _allModuleString = string.Empty;
		private string _scannerString = string.Empty;

		public ChooseScannerForm()
		{
			InitializeComponent();

			_allModuleString = Nffv.GetAvailableScannerModules();
			if (_allModuleString.Length > 0)
			{
				string[] allModuleList = _allModuleString.Split(new char[] { ';' });
				clbScannerList.Items.Clear();
				clbScannerList.Items.AddRange(allModuleList);
			}
			else
			{
				clbScannerList.Items.Add("No scanner modules found.");
				clbScannerList.Enabled = false;
			}
		}

		private void btnOK_Click(object sender, EventArgs e)
		{
			if (clbScannerList.CheckedItems.Count == 0)
			{
				DialogResult = DialogResult.None;
				MessageBox.Show("No scanners were selected.", "Nffv C# Sample", MessageBoxButtons.OK, MessageBoxIcon.Warning);
				return;
			}
			if (_allModuleString.Length > 0)
			{
				StringBuilder scannerString = new StringBuilder();
				foreach (string selItem in clbScannerList.CheckedItems)
				{
					if (scannerString.Length > 0)
					{
						scannerString.Append(";");
					}
					scannerString.Append(selItem);
				}
				_scannerString = scannerString.ToString();
				Close();
			}
		}

		public string ScannerString
		{
			get
			{
				return _scannerString;
			}
		}

		public string FingerprintDatabase
		{
			get
			{
				return tbDatabaseName.Text;
			}
			set
			{
				tbDatabaseName.Text = value;
			}
		}

		public string FingerprintDatabasePassword
		{
			get
			{
				return tbPassword.Text;
			}
			set
			{
				tbPassword.Text = value;
			}
		}

		public string UserDatabase
		{
			get
			{
				return tbUserDatabase.Text;
			}
			set
			{
				tbUserDatabase.Text = value;
			}
		}
	}
}
