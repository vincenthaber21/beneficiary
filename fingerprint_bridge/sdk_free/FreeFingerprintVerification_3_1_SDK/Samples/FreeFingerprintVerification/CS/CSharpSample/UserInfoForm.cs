using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;

namespace CSharpSample
{
	public partial class UserInfoForm : Form
	{
		public UserInfoForm()
		{
			InitializeComponent();
		}

		public string UserName
		{
			get
			{
				return lblUserName.Text;
			}
			set
			{
				lblUserName.Text = value;
			}
		}

		public Image UserFingerprintImage
		{
			get
			{
				return pbUserFinger.Image;
			}
			set
			{
				pbUserFinger.Image = value;
			}
		}
	}
}
