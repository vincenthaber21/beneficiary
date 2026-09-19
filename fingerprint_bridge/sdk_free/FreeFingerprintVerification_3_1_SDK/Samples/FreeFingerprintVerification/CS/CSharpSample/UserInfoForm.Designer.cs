namespace CSharpSample
{
	partial class UserInfoForm
	{
		/// <summary>
		/// Required designer variable.
		/// </summary>
		private System.ComponentModel.IContainer components = null;

		/// <summary>
		/// Clean up any resources being used.
		/// </summary>
		/// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
		protected override void Dispose(bool disposing)
		{
			if (disposing && (components != null))
			{
				components.Dispose();
			}
			base.Dispose(disposing);
		}

		#region Windows Form Designer generated code

		/// <summary>
		/// Required method for Designer support - do not modify
		/// the contents of this method with the code editor.
		/// </summary>
		private void InitializeComponent()
		{
			this.btnClose = new System.Windows.Forms.Button();
			this.lblUserName = new System.Windows.Forms.Label();
			this.pbUserFinger = new System.Windows.Forms.PictureBox();
			((System.ComponentModel.ISupportInitialize)(this.pbUserFinger)).BeginInit();
			this.SuspendLayout();
			// 
			// btnClose
			// 
			this.btnClose.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Right)));
			this.btnClose.DialogResult = System.Windows.Forms.DialogResult.Cancel;
			this.btnClose.Location = new System.Drawing.Point(356, 527);
			this.btnClose.Name = "btnClose";
			this.btnClose.Size = new System.Drawing.Size(75, 23);
			this.btnClose.TabIndex = 0;
			this.btnClose.Text = "Close";
			this.btnClose.UseVisualStyleBackColor = true;
			// 
			// lblUserName
			// 
			this.lblUserName.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left)
						| System.Windows.Forms.AnchorStyles.Right)));
			this.lblUserName.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
			this.lblUserName.Location = new System.Drawing.Point(4, 6);
			this.lblUserName.Name = "lblUserName";
			this.lblUserName.Size = new System.Drawing.Size(427, 23);
			this.lblUserName.TabIndex = 1;
			this.lblUserName.Text = "label1";
			this.lblUserName.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
			// 
			// pbUserFinger
			// 
			this.pbUserFinger.Anchor = ((System.Windows.Forms.AnchorStyles)((((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom)
						| System.Windows.Forms.AnchorStyles.Left)
						| System.Windows.Forms.AnchorStyles.Right)));
			this.pbUserFinger.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
			this.pbUserFinger.Location = new System.Drawing.Point(4, 32);
			this.pbUserFinger.Name = "pbUserFinger";
			this.pbUserFinger.Size = new System.Drawing.Size(427, 489);
			this.pbUserFinger.SizeMode = System.Windows.Forms.PictureBoxSizeMode.CenterImage;
			this.pbUserFinger.TabIndex = 2;
			this.pbUserFinger.TabStop = false;
			// 
			// UserInfoForm
			// 
			this.AcceptButton = this.btnClose;
			this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
			this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
			this.CancelButton = this.btnClose;
			this.ClientSize = new System.Drawing.Size(436, 562);
			this.Controls.Add(this.pbUserFinger);
			this.Controls.Add(this.lblUserName);
			this.Controls.Add(this.btnClose);
			this.MinimizeBox = false;
			this.Name = "UserInfoForm";
			this.ShowIcon = false;
			this.ShowInTaskbar = false;
			this.Text = "User Information";
			((System.ComponentModel.ISupportInitialize)(this.pbUserFinger)).EndInit();
			this.ResumeLayout(false);

		}

		#endregion

		private System.Windows.Forms.Button btnClose;
		private System.Windows.Forms.Label lblUserName;
		private System.Windows.Forms.PictureBox pbUserFinger;
	}
}
