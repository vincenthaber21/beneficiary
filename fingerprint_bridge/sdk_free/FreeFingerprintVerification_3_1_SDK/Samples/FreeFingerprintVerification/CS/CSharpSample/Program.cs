
using System;
using System.Collections.Generic;
using System.Windows.Forms;

namespace CSharpSample
{
	static class Program
	{
		/// <summary>
		/// The main entry point for the application.
		/// </summary>
		[STAThread]
		static void Main()
		{
			Application.EnableVisualStyles();
			Application.SetCompatibleTextRenderingDefault(false);

			Neurotec.Biometrics.Nffv engine = null;
			try
			{
				ChooseScannerForm chooseScannerForm = new ChooseScannerForm();
				if (chooseScannerForm.ShowDialog() == DialogResult.OK)
				{
					try
					{
						engine = new Neurotec.Biometrics.Nffv(chooseScannerForm.FingerprintDatabase, chooseScannerForm.FingerprintDatabasePassword, chooseScannerForm.ScannerString);
					}
					catch (Exception)
					{
						MessageBox.Show("Failed to initialize Nffv or create/load database.\r\n" +
						"Please check if:\r\n - Provided password is correct;\r\n - Database filename is correct;\r\n" +
						" - Scanners are used properly.\r\n", "Nffv C# Sample", MessageBoxButtons.OK, MessageBoxIcon.Error);
						return;
					}
					Application.Run(new MainForm(engine, chooseScannerForm.UserDatabase));
				}
			}
			catch (Exception ex)
			{
				MessageBox.Show(
					string.Format("An error has occured: {0}", ex.Message), "Nffv C# Sample",
					MessageBoxButtons.OK, MessageBoxIcon.Error);
			}
			finally
			{
				if (engine != null)
				{
					engine.Dispose();
				}
			}
		}
	}
}
