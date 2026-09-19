using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Diagnostics;

using Neurotec;
using Neurotec.Biometrics;

namespace CSharpSample
{
	public partial class AboutForm : Form
	{
		[DllImport("kernel32.dll", CharSet = CharSet.Auto)]
		private static extern IntPtr LoadLibrary(string fileName);

		public AboutForm()
		{
			InitializeComponent();

			lblCopyright1.Text = Application.ProductName + " " + Application.ProductVersion;
			lblCopyright2.Text = "Copyright ??? 2008-2026 Neurotechnology";

			string OSName = System.Environment.OSVersion.Platform.ToString();
			lblOS.Text = string.Format("{0}. Version {1}.{2} (Build {3})",
				OSName ?? "Windows",
				System.Environment.OSVersion.Version.Major,
				System.Environment.OSVersion.Version.Minor,
				System.Environment.OSVersion.Version.Build);

			lblServicePack.Text = System.Environment.OSVersion.ServicePack;

			componentsListView.BeginUpdate();
			AddComponentInfo(this.GetType());
			componentsListView.Items.Add(new ListViewItem(new string[]
				{
					"Microsoft .NET Framework",
					Environment.Version.ToString(),
					null
				}));
			componentsListView.Items.Add(new ListViewItem(new string[]
				{
					"    " + Environment.OSVersion.VersionString,
					Environment.OSVersion.Version.ToString(),
					null
				}));
			AddComponentInfo(typeof(Nffv));
			componentColumnHeader.AutoResize(ColumnHeaderAutoResizeStyle.ColumnContent);
			versionColumnHeader.AutoResize(ColumnHeaderAutoResizeStyle.ColumnContent);
			copyrightColumnHeader.AutoResize(ColumnHeaderAutoResizeStyle.ColumnContent);
			componentsListView.EndUpdate();
		}

		private void AddComponentInfo(Type type)
		{

			string dllName = null;
			FieldInfo dllNameFieldInfo = type.GetField("DllName");
			if (dllNameFieldInfo != null && dllNameFieldInfo.FieldType == typeof(string) && dllNameFieldInfo.IsStatic)
			{
				dllName = (string)dllNameFieldInfo.GetValue(null);
			}

			Assembly assembly = type.Assembly;
			AssemblyTitleAttribute assemblyTitleAttribute = (AssemblyTitleAttribute)assembly.GetCustomAttributes(typeof(AssemblyTitleAttribute), false)[0];
			Version version = assembly.GetName().Version;
			AssemblyInformationalVersionAttribute[] assemblyInformationalVersionAttributes = (AssemblyInformationalVersionAttribute[])assembly.GetCustomAttributes(typeof(AssemblyInformationalVersionAttribute), false);
			AssemblyCopyrightAttribute assemblyCopyrightAttribute = (AssemblyCopyrightAttribute)assembly.GetCustomAttributes(typeof(AssemblyCopyrightAttribute), false)[0];

			FileVersionInfo dllVersionInfo = null;
			if (dllName != null)
			{
				IntPtr hModule = LoadLibrary(dllName);
				dllVersionInfo = FileVersionInfo.GetVersionInfo(dllName);
			}
			ListViewItem listViewItem = new ListViewItem(new string[]
				{
					assemblyTitleAttribute.Title,
					assemblyInformationalVersionAttributes.Length == 0 ? version.ToString() : assemblyInformationalVersionAttributes[0].InformationalVersion,
					assemblyCopyrightAttribute.Copyright
				});
			componentsListView.Items.Add(listViewItem);
			if (dllVersionInfo != null)
			{
				componentsListView.Items.Add(new ListViewItem(new string[]
				{
					"    " + dllVersionInfo.FileDescription,
					new Version(dllVersionInfo.FileMajorPart, dllVersionInfo.FileMinorPart, dllVersionInfo.FileBuildPart, dllVersionInfo.FilePrivatePart).ToString(),
					null,
					dllVersionInfo.LegalCopyright
				}));
			}
		}
	}
}
