namespace CSharpSample
{
	partial class MainForm
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
		System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(MainForm));
		this.toolStrip1 = new System.Windows.Forms.ToolStrip();
		this.btnEnroll = new System.Windows.Forms.ToolStripButton();
		this.btnVerify = new System.Windows.Forms.ToolStripButton();
		this.toolStripSeparator2 = new System.Windows.Forms.ToolStripSeparator();
		this.btnDeleteUser = new System.Windows.Forms.ToolStripButton();
		this.btnClearDatabase = new System.Windows.Forms.ToolStripButton();
		this.toolStripSeparator1 = new System.Windows.Forms.ToolStripSeparator();
		this.btnSettings = new System.Windows.Forms.ToolStripButton();
		this.toolStripSeparator3 = new System.Windows.Forms.ToolStripSeparator();
		this.btnAbout = new System.Windows.Forms.ToolStripButton();
		this.splitContainer1 = new System.Windows.Forms.SplitContainer();
		this.pbExtractedImage = new System.Windows.Forms.PictureBox();
		this.tlpLeft = new System.Windows.Forms.TableLayoutPanel();
		this.lbDatabase = new System.Windows.Forms.ListBox();
		this.label1 = new System.Windows.Forms.Label();
		this.statusStrip1 = new System.Windows.Forms.StatusStrip();
		this.toolStrip1.SuspendLayout();
		((System.ComponentModel.ISupportInitialize)(this.splitContainer1)).BeginInit();
		this.splitContainer1.Panel1.SuspendLayout();
		this.splitContainer1.Panel2.SuspendLayout();
		this.splitContainer1.SuspendLayout();
		((System.ComponentModel.ISupportInitialize)(this.pbExtractedImage)).BeginInit();
		this.tlpLeft.SuspendLayout();
		this.SuspendLayout();
		// 
		// toolStrip1
		// 
		this.toolStrip1.Items.AddRange(new System.Windows.Forms.ToolStripItem[] {
		this.btnEnroll,
		this.btnVerify,
		this.toolStripSeparator2,
		this.btnDeleteUser,
		this.btnClearDatabase,
		this.toolStripSeparator1,
		this.btnSettings,
		this.toolStripSeparator3,
		this.btnAbout});
		this.toolStrip1.Location = new System.Drawing.Point(0, 0);
		this.toolStrip1.Name = "toolStrip1";
		this.toolStrip1.Size = new System.Drawing.Size(607, 25);
		this.toolStrip1.TabIndex = 0;
		this.toolStrip1.Text = "toolStrip1";
		// 
		// btnEnroll
		// 
		this.btnEnroll.DisplayStyle = System.Windows.Forms.ToolStripItemDisplayStyle.Text;
		this.btnEnroll.Font = new System.Drawing.Font("Tahoma", 9.75F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
		this.btnEnroll.ImageTransparentColor = System.Drawing.Color.Magenta;
		this.btnEnroll.Name = "btnEnroll";
		this.btnEnroll.Size = new System.Drawing.Size(47, 22);
		this.btnEnroll.Text = "Enroll";
		this.btnEnroll.Click += new System.EventHandler(this.btnEnroll_Click);
		// 
		// btnVerify
		// 
		this.btnVerify.DisplayStyle = System.Windows.Forms.ToolStripItemDisplayStyle.Text;
		this.btnVerify.Font = new System.Drawing.Font("Tahoma", 9.75F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
		this.btnVerify.ImageTransparentColor = System.Drawing.Color.Magenta;
		this.btnVerify.Name = "btnVerify";
		this.btnVerify.Size = new System.Drawing.Size(51, 22);
		this.btnVerify.Text = "Verify";
		this.btnVerify.Click += new System.EventHandler(this.btnVerify_Click);
		// 
		// toolStripSeparator2
		// 
		this.toolStripSeparator2.Name = "toolStripSeparator2";
		this.toolStripSeparator2.Size = new System.Drawing.Size(6, 25);
		// 
		// btnDeleteUser
		// 
		this.btnDeleteUser.Image = global::CSharpSample.Properties.Resources.Delete;
		this.btnDeleteUser.ImageTransparentColor = System.Drawing.Color.Magenta;
		this.btnDeleteUser.Name = "btnDeleteUser";
		this.btnDeleteUser.Size = new System.Drawing.Size(85, 22);
		this.btnDeleteUser.Text = "Delete user";
		this.btnDeleteUser.Click += new System.EventHandler(this.btnDeleteUser_Click);
		// 
		// btnClearDatabase
		// 
		this.btnClearDatabase.Image = global::CSharpSample.Properties.Resources.DeleteFolderHS;
		this.btnClearDatabase.ImageTransparentColor = System.Drawing.Color.Magenta;
		this.btnClearDatabase.Name = "btnClearDatabase";
		this.btnClearDatabase.Size = new System.Drawing.Size(105, 22);
		this.btnClearDatabase.Text = "Clear Database";
		this.btnClearDatabase.Click += new System.EventHandler(this.btnClearDatabase_Click);
		// 
		// toolStripSeparator1
		// 
		this.toolStripSeparator1.Name = "toolStripSeparator1";
		this.toolStripSeparator1.Size = new System.Drawing.Size(6, 25);
		// 
		// btnSettings
		// 
		this.btnSettings.Image = global::CSharpSample.Properties.Resources.OptionsHS;
		this.btnSettings.ImageTransparentColor = System.Drawing.Color.Magenta;
		this.btnSettings.Name = "btnSettings";
		this.btnSettings.Size = new System.Drawing.Size(69, 22);
		this.btnSettings.Text = "Settings";
		this.btnSettings.Click += new System.EventHandler(this.btnSettings_Click);
		// 
		// toolStripSeparator3
		// 
		this.toolStripSeparator3.Name = "toolStripSeparator3";
		this.toolStripSeparator3.Size = new System.Drawing.Size(6, 25);
		// 
		// btnAbout
		// 
		this.btnAbout.Image = global::CSharpSample.Properties.Resources.Info;
		this.btnAbout.ImageTransparentColor = System.Drawing.Color.Magenta;
		this.btnAbout.Name = "btnAbout";
		this.btnAbout.Size = new System.Drawing.Size(60, 22);
		this.btnAbout.Text = "About";
		this.btnAbout.Click += new System.EventHandler(this.btnAbout_Click);
		// 
		// splitContainer1
		// 
		this.splitContainer1.Dock = System.Windows.Forms.DockStyle.Fill;
		this.splitContainer1.Location = new System.Drawing.Point(0, 25);
		this.splitContainer1.Name = "splitContainer1";
		// 
		// splitContainer1.Panel1
		// 
		this.splitContainer1.Panel1.Controls.Add(this.pbExtractedImage);
		// 
		// splitContainer1.Panel2
		// 
		this.splitContainer1.Panel2.Controls.Add(this.tlpLeft);
		this.splitContainer1.Size = new System.Drawing.Size(607, 351);
		this.splitContainer1.SplitterDistance = 416;
		this.splitContainer1.TabIndex = 1;
		// 
		// pbExtractedImage
		// 
		this.pbExtractedImage.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
		this.pbExtractedImage.Dock = System.Windows.Forms.DockStyle.Fill;
		this.pbExtractedImage.Location = new System.Drawing.Point(0, 0);
		this.pbExtractedImage.Name = "pbExtractedImage";
		this.pbExtractedImage.Size = new System.Drawing.Size(416, 351);
		this.pbExtractedImage.SizeMode = System.Windows.Forms.PictureBoxSizeMode.CenterImage;
		this.pbExtractedImage.TabIndex = 0;
		this.pbExtractedImage.TabStop = false;
		// 
		// tlpLeft
		// 
		this.tlpLeft.ColumnCount = 1;
		this.tlpLeft.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100F));
		this.tlpLeft.Controls.Add(this.lbDatabase, 0, 1);
		this.tlpLeft.Controls.Add(this.label1, 0, 0);
		this.tlpLeft.Dock = System.Windows.Forms.DockStyle.Fill;
		this.tlpLeft.Location = new System.Drawing.Point(0, 0);
		this.tlpLeft.Name = "tlpLeft";
		this.tlpLeft.RowCount = 2;
		this.tlpLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 27F));
		this.tlpLeft.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
		this.tlpLeft.Size = new System.Drawing.Size(187, 351);
		this.tlpLeft.TabIndex = 0;
		// 
		// lbDatabase
		// 
		this.lbDatabase.Dock = System.Windows.Forms.DockStyle.Fill;
		this.lbDatabase.FormattingEnabled = true;
		this.lbDatabase.Location = new System.Drawing.Point(3, 30);
		this.lbDatabase.Name = "lbDatabase";
		this.lbDatabase.Size = new System.Drawing.Size(181, 318);
		this.lbDatabase.TabIndex = 1;
		this.lbDatabase.SelectedIndexChanged += new System.EventHandler(this.lbDatabase_SelectedIndexChanged);
		this.lbDatabase.DoubleClick += new System.EventHandler(this.lbDatabase_DoubleClick);
		// 
		// label1
		// 
		this.label1.AutoSize = true;
		this.label1.Dock = System.Windows.Forms.DockStyle.Fill;
		this.label1.Location = new System.Drawing.Point(3, 0);
		this.label1.Name = "label1";
		this.label1.Size = new System.Drawing.Size(181, 27);
		this.label1.TabIndex = 2;
		this.label1.Text = "User list:";
		this.label1.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
		// 
		// statusStrip1
		// 
		this.statusStrip1.Location = new System.Drawing.Point(0, 376);
		this.statusStrip1.Name = "statusStrip1";
		this.statusStrip1.Size = new System.Drawing.Size(607, 22);
		this.statusStrip1.TabIndex = 2;
		this.statusStrip1.Text = "statusStrip1";
		// 
		// MainForm
		// 
		this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
		this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
		this.ClientSize = new System.Drawing.Size(607, 398);
		this.Controls.Add(this.splitContainer1);
		this.Controls.Add(this.toolStrip1);
		this.Controls.Add(this.statusStrip1);
		this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
		this.Name = "MainForm";
		this.Text = "Nffv C# Sample";
		this.Load += new System.EventHandler(this.MainForm_Load);
		this.toolStrip1.ResumeLayout(false);
		this.toolStrip1.PerformLayout();
		this.splitContainer1.Panel1.ResumeLayout(false);
		this.splitContainer1.Panel2.ResumeLayout(false);
		((System.ComponentModel.ISupportInitialize)(this.splitContainer1)).EndInit();
		this.splitContainer1.ResumeLayout(false);
		((System.ComponentModel.ISupportInitialize)(this.pbExtractedImage)).EndInit();
		this.tlpLeft.ResumeLayout(false);
		this.tlpLeft.PerformLayout();
		this.ResumeLayout(false);
		this.PerformLayout();
      
		}

		#endregion

		private System.Windows.Forms.ToolStrip toolStrip1;
		private System.Windows.Forms.ToolStripButton btnEnroll;
		private System.Windows.Forms.ToolStripButton btnVerify;
		private System.Windows.Forms.SplitContainer splitContainer1;
		private System.Windows.Forms.PictureBox pbExtractedImage;
		private System.Windows.Forms.StatusStrip statusStrip1;
		private System.Windows.Forms.ToolStripSeparator toolStripSeparator1;
		private System.Windows.Forms.ToolStripButton btnDeleteUser;
		private System.Windows.Forms.ToolStripButton btnSettings;
		private System.Windows.Forms.ToolStripSeparator toolStripSeparator2;
		private System.Windows.Forms.ToolStripButton btnClearDatabase;
		private System.Windows.Forms.ToolStripSeparator toolStripSeparator3;
		private System.Windows.Forms.ToolStripButton btnAbout;
		private System.Windows.Forms.TableLayoutPanel tlpLeft;
		private System.Windows.Forms.ListBox lbDatabase;
		private System.Windows.Forms.Label label1;

	}
}

