using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;

using Neurotec.Biometrics;
using System.Globalization;

namespace CSharpSample
{
	public partial class SettingsForm : Form
	{
		public SettingsForm()
		{
			InitializeComponent();

			cbMatchingThreshold.BeginUpdate();
			cbMatchingThreshold.Items.Add(0.001.ToString("P1"));
			cbMatchingThreshold.Items.Add(0.0001.ToString("P2"));
			cbMatchingThreshold.Items.Add(0.00001.ToString("P3"));
			cbMatchingThreshold.EndUpdate();
		}

		public void LoadFromEngine(Nffv engine)
		{
			nudQualityThreshold.Value = Convert.ToDecimal(engine.QualityThreshold);
			cbMatchingThreshold.Text = MatchingThresholdToString(engine.MatchingThreshold);
		}

		public void SaveToEngine(Nffv engine)
		{
			engine.QualityThreshold = Convert.ToByte(nudQualityThreshold.Value);
			engine.MatchingThreshold = MatchingThresholdFromString(cbMatchingThreshold.Text);
		}

		private static string MatchingThresholdToString(int value)
		{
			double p = -value / 12.0;
			return string.Format(string.Format("{{0:P{0}}}", Math.Max(0, (int)Math.Ceiling(-p) - 2)), Math.Pow(10, p));
		}

		private static int MatchingThresholdFromString(string value)
		{
			double p = Math.Log10(Math.Max(double.Epsilon, Math.Min(1,
				double.Parse(value.Replace(CultureInfo.CurrentCulture.NumberFormat.PercentSymbol, "")) / 100)));
			return Math.Max(0, (int)Math.Round(-12 * p));
		}

		private void SettingsForm_Validating(object sender, CancelEventArgs e)
		{
			try
			{
				MatchingThresholdFromString(cbMatchingThreshold.ValueMember);
			}
			catch
			{
				errorProvider1.SetError(cbMatchingThreshold, "Matching threshold value is invalid.");
				e.Cancel = true;
			}
		}
	}
}
