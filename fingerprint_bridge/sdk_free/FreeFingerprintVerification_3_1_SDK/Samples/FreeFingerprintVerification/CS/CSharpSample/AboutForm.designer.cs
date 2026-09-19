namespace CSharpSample
{
    partial class AboutForm
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
			this.pictureBox1 = new System.Windows.Forms.PictureBox();
			this.lblCopyright1 = new System.Windows.Forms.Label();
			this.lblCopyright2 = new System.Windows.Forms.Label();
			this.groupBox1 = new System.Windows.Forms.GroupBox();
			this.lblServicePack = new System.Windows.Forms.Label();
			this.lblOS = new System.Windows.Forms.Label();
			this.groupBox2 = new System.Windows.Forms.GroupBox();
			this.componentsListView = new System.Windows.Forms.ListView();
			this.componentColumnHeader = new System.Windows.Forms.ColumnHeader();
			this.versionColumnHeader = new System.Windows.Forms.ColumnHeader();
			this.copyrightColumnHeader = new System.Windows.Forms.ColumnHeader();
			((System.ComponentModel.ISupportInitialize)(this.pictureBox1)).BeginInit();
			this.groupBox1.SuspendLayout();
			this.groupBox2.SuspendLayout();
			this.SuspendLayout();
			// 
			// pictureBox1
			// 
			this.pictureBox1.BackColor = System.Drawing.SystemColors.Window;
			this.pictureBox1.Image = global::CSharpSample.Properties.Resources.Neurotechnology;
			this.pictureBox1.Location = new System.Drawing.Point(12, 12);
			this.pictureBox1.Name = "pictureBox1";
			this.pictureBox1.Size = new System.Drawing.Size(230, 80);
			this.pictureBox1.SizeMode = System.Windows.Forms.PictureBoxSizeMode.AutoSize;
			this.pictureBox1.TabIndex = 0;
			this.pictureBox1.TabStop = false;
			// 
			// lblCopyright1
			// 
			this.lblCopyright1.AutoSize = true;
			this.lblCopyright1.Location = new System.Drawing.Point(12, 105);
			this.lblCopyright1.Name = "lblCopyright1";
			this.lblCopyright1.Size = new System.Drawing.Size(92, 13);
			this.lblCopyright1.TabIndex = 1;
			this.lblCopyright1.Text = "VeriFinger Sample";
			// 
			// lblCopyright2
			// 
			this.lblCopyright2.AutoSize = true;
			this.lblCopyright2.Location = new System.Drawing.Point(12, 120);
			this.lblCopyright2.Name = "lblCopyright2";
			this.lblCopyright2.Size = new System.Drawing.Size(51, 13);
			this.lblCopyright2.TabIndex = 2;
			this.lblCopyright2.Text = "Copyright";
			// 
			// groupBox1
			// 
			this.groupBox1.Controls.Add(this.lblServicePack);
			this.groupBox1.Controls.Add(this.lblOS);
			this.groupBox1.Location = new System.Drawing.Point(12, 140);
			this.groupBox1.Name = "groupBox1";
			this.groupBox1.Size = new System.Drawing.Size(411, 60);
			this.groupBox1.TabIndex = 3;
			this.groupBox1.TabStop = false;
			this.groupBox1.Text = "Operating system";
			// 
			// lblServicePack
			// 
			this.lblServicePack.AutoSize = true;
			this.lblServicePack.Location = new System.Drawing.Point(6, 35);
			this.lblServicePack.Name = "lblServicePack";
			this.lblServicePack.Size = new System.Drawing.Size(21, 13);
			this.lblServicePack.TabIndex = 5;
			this.lblServicePack.Text = "SP";
			// 
			// lblOS
			// 
			this.lblOS.AutoSize = true;
			this.lblOS.Location = new System.Drawing.Point(6, 19);
			this.lblOS.Name = "lblOS";
			this.lblOS.Size = new System.Drawing.Size(22, 13);
			this.lblOS.TabIndex = 4;
			this.lblOS.Text = "OS";
			// 
			// groupBox2
			// 
			this.groupBox2.Controls.Add(this.componentsListView);
			this.groupBox2.Location = new System.Drawing.Point(12, 206);
			this.groupBox2.Name = "groupBox2";
			this.groupBox2.Size = new System.Drawing.Size(411, 206);
			this.groupBox2.TabIndex = 4;
			this.groupBox2.TabStop = false;
			this.groupBox2.Text = "Components";
			// 
			// componentsListView
			// 
			this.componentsListView.Columns.AddRange(new System.Windows.Forms.ColumnHeader[] {
            this.componentColumnHeader,
            this.versionColumnHeader,
            this.copyrightColumnHeader});
			this.componentsListView.Dock = System.Windows.Forms.DockStyle.Fill;
			this.componentsListView.FullRowSelect = true;
			this.componentsListView.HeaderStyle = System.Windows.Forms.ColumnHeaderStyle.Nonclickable;
			this.componentsListView.Location = new System.Drawing.Point(3, 16);
			this.componentsListView.Name = "componentsListView";
			this.componentsListView.Size = new System.Drawing.Size(405, 187);
			this.componentsListView.TabIndex = 16;
			this.componentsListView.UseCompatibleStateImageBehavior = false;
			this.componentsListView.View = System.Windows.Forms.View.Details;
			// 
			// componentColumnHeader
			// 
			this.componentColumnHeader.Text = "Component";
			this.componentColumnHeader.Width = 300;
			// 
			// versionColumnHeader
			// 
			this.versionColumnHeader.Text = "Version";
			this.versionColumnHeader.Width = 100;
			// 
			// copyrightColumnHeader
			// 
			this.copyrightColumnHeader.Text = "Copyright";
			this.copyrightColumnHeader.Width = 200;
			// 
			// AboutForm
			// 
			this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
			this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
			this.BackColor = System.Drawing.SystemColors.Window;
			this.ClientSize = new System.Drawing.Size(435, 421);
			this.Controls.Add(this.groupBox2);
			this.Controls.Add(this.groupBox1);
			this.Controls.Add(this.lblCopyright2);
			this.Controls.Add(this.lblCopyright1);
			this.Controls.Add(this.pictureBox1);
			this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedToolWindow;
			this.MaximizeBox = false;
			this.MinimizeBox = false;
			this.Name = "AboutForm";
			this.ShowInTaskbar = false;
			this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
			this.Text = "About";
			((System.ComponentModel.ISupportInitialize)(this.pictureBox1)).EndInit();
			this.groupBox1.ResumeLayout(false);
			this.groupBox1.PerformLayout();
			this.groupBox2.ResumeLayout(false);
			this.ResumeLayout(false);
			this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.PictureBox pictureBox1;
        private System.Windows.Forms.Label lblCopyright1;
        private System.Windows.Forms.Label lblCopyright2;
        private System.Windows.Forms.GroupBox groupBox1;
        private System.Windows.Forms.Label lblServicePack;
        private System.Windows.Forms.Label lblOS;
        private System.Windows.Forms.GroupBox groupBox2;
        private System.Windows.Forms.ListView componentsListView;
        private System.Windows.Forms.ColumnHeader componentColumnHeader;
		private System.Windows.Forms.ColumnHeader versionColumnHeader;
        private System.Windows.Forms.ColumnHeader copyrightColumnHeader;
    }
}
