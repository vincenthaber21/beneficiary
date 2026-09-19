using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Drawing;
using System.Windows.Forms;
using System.Reflection;

namespace CSharpSample
{
	partial class EnrollForm : Form
	{
		public EnrollForm()
		{
			InitializeComponent();
		}

		public string UserName
		{
			get
			{
				return tbUserName.Text;
			}
			set
			{
				tbUserName.Text = value;
			}
		}
	}
}
