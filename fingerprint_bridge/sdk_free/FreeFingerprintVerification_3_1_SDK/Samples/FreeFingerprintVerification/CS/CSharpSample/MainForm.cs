using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;

using Neurotec.Biometrics;
using Neurotec.Gui;

namespace CSharpSample
{
	public partial class MainForm : Form
	{
		Nffv _engine;
		string _userDatabaseFile;
		UserDatabase _userDB;

		public MainForm(Nffv engine, string userDatabaseFile)
		{
			_engine = engine;

			_userDatabaseFile = userDatabaseFile;
			try
			{
				_userDB = UserDatabase.ReadFromFile(userDatabaseFile);
			}
			catch
			{
				_userDB = new UserDatabase();
			}

			InitializeComponent();
		}

		private void MainForm_Load(object sender, EventArgs e)
		{
			foreach (NffvUser engineUser in _engine.Users)
			{
				string id = engineUser.Id.ToString();
				UserRecord userRec = _userDB.Lookup(engineUser.Id);
				if (userRec != null)
				{
					id = userRec.Name;
				}
				lbDatabase.Items.Add(new CData(engineUser, id));
			}
			if (lbDatabase.Items.Count > 0)
				lbDatabase.SelectedIndex = 0;
		}

		internal class EnrollmentResult
		{
			public NffvStatus engineStatus;
			public NffvUser engineUser;
		};

		private void btnEnroll_Click(object sender, EventArgs e)
		{
			EnrollForm enrollDlg = new EnrollForm();
			if (_engine.Users.Count >= Nffv.MaxUserCount)
			{
				MessageBox.Show("Maximum number of users is reached.");
				return;
			}
			if (enrollDlg.ShowDialog() == DialogResult.OK)
			{
				try
				{
					RunWorkerCompletedEventArgs taskResult = BusyForm.RunLongTask("Waiting for fingerprint ...", new DoWorkEventHandler(doEnroll),
						false, null, new EventHandler(CancelScanningHandler));
					EnrollmentResult enrollmentResult = (EnrollmentResult)taskResult.Result;
					if (enrollmentResult.engineStatus == NffvStatus.TemplateCreated)
					{
						NffvUser engineUser = enrollmentResult.engineUser;
						string userName = enrollDlg.UserName;
						if (userName.Length <= 0)
						{
							userName = engineUser.Id.ToString();
						}

						_userDB.Add(new UserRecord(engineUser.Id, userName));
						try
						{
							_userDB.WriteToFile(_userDatabaseFile);
						}
						catch { }

						pbExtractedImage.Image = engineUser.GetBitmap();
						lbDatabase.Items.Add(new CData(engineUser, userName));
						lbDatabase.SelectedIndex = lbDatabase.Items.Count - 1;
					}
					else
					{
						NffvStatus engineStatus = enrollmentResult.engineStatus;
						MessageBox.Show(string.Format("Enrollment was not finished. Reason: {0}", engineStatus));
					}
				}
				catch (Exception ex)
				{
					MessageBox.Show(ex.Message);
				}
			}
		}

		private void doEnroll(object sender, DoWorkEventArgs args)
		{
			EnrollmentResult enrollmentResults = new EnrollmentResult();
			enrollmentResults.engineUser = _engine.Enroll(20000, out enrollmentResults.engineStatus);
			args.Result = enrollmentResults;
		}

		internal class VerificationResult
		{
			public NffvStatus engineStatus;
			public int score;
		};

		private void btnVerify_Click(object sender, EventArgs e)
		{
			if (lbDatabase.SelectedIndex < 0)
			{
				MessageBox.Show("Please select a record from the database.");
			}
			else
			{
				try
				{
					RunWorkerCompletedEventArgs taskResult = BusyForm.RunLongTask("Waiting for fingerprint ...", new DoWorkEventHandler(doVerify),
						false, ((CData)lbDatabase.SelectedItem).EngineUser, new EventHandler(CancelScanningHandler));
					VerificationResult verificationResult = (VerificationResult)taskResult.Result;
					if (verificationResult.engineStatus == NffvStatus.TemplateCreated)
					{
						if (verificationResult.score > 0)
						{
							MessageBox.Show(string.Format("{0} verified.\r\nFingerprints match. Score: {1}", ((CData)lbDatabase.SelectedItem).Name, verificationResult.score));
						}
						else
						{
							MessageBox.Show(string.Format("{0} not verified.\r\nFingerprints do not match. Score: {1}", ((CData)lbDatabase.SelectedItem).Name, verificationResult.score));
						}
					}
					else
					{
						MessageBox.Show(string.Format("Verification was not finished. Reason: {0}", verificationResult.engineStatus));
					}
				}
				catch (Exception ex)
				{
					MessageBox.Show(ex.Message);
				}
			}
		}

		private void doVerify(object sender, DoWorkEventArgs args)
		{
			VerificationResult verificationResult = new VerificationResult();
			verificationResult.score = _engine.Verify((NffvUser)args.Argument, 20000, out verificationResult.engineStatus);
			args.Result = verificationResult;
		}

		private void CancelScanningHandler(object sender, EventArgs e)
		{
			_engine.Cancel();
		}

		private void btnDeleteUser_Click(object sender, EventArgs e)
		{
			if (lbDatabase.SelectedIndex < 0)
			{
				MessageBox.Show("Please select a record from the database.");
			}
			else
			{
				_userDB.Remove(_userDB.Lookup(((CData)lbDatabase.SelectedItem).ID));
				try
				{
					_userDB.WriteToFile(_userDatabaseFile);
				}
				catch { }

				_engine.Users.RemoveAt(lbDatabase.SelectedIndex);
				lbDatabase.Items.RemoveAt(lbDatabase.SelectedIndex);
				if (lbDatabase.Items.Count > 0)
					lbDatabase.SelectedIndex = 0;
			}
		}

		private void btnClearDatabase_Click(object sender, EventArgs e)
		{
			if (MessageBox.Show("All records will be deleted from database. Do you want to continue?", "Confirm delete", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes)
			{
				return;
			}

			_engine.Users.Clear();
			lbDatabase.Items.Clear();

			_userDB.Clear();
			try
			{
				_userDB.WriteToFile(_userDatabaseFile);
			}
			catch { }
		}

		private void btnSettings_Click(object sender, EventArgs e)
		{
			SettingsForm settingsForm = new SettingsForm();
			settingsForm.LoadFromEngine(_engine);
			if (settingsForm.ShowDialog() == DialogResult.OK)
			{
				settingsForm.SaveToEngine(_engine);
			}
		}

		private void btnAbout_Click(object sender, EventArgs e)
		{
			AboutForm aboutForm = new AboutForm();
			aboutForm.ShowDialog();
		}

		private void lbDatabase_DoubleClick(object sender, EventArgs e)
		{
			if (lbDatabase.SelectedItem != null)
			{
				CData userData = (CData)lbDatabase.SelectedItem;
				UserInfoForm userInfoForm = new UserInfoForm();
				userInfoForm.UserName = userData.Name;
				userInfoForm.UserFingerprintImage = userData.Image;
				userInfoForm.ShowDialog();
			}
		}

		private void lbDatabase_SelectedIndexChanged(object sender, EventArgs e)
		{
			if (lbDatabase.SelectedItem != null)
			{
				CData userData = (CData)lbDatabase.SelectedItem;
				pbExtractedImage.Image = userData.Image;
			}
		}
	}

	class CData : IDisposable
	{
		private NffvUser _engineUser;
		private Bitmap _image;
		private string _name;

		public CData(NffvUser engineUser, string name)
		{
			_engineUser = engineUser;
			_image = engineUser.GetBitmap();
			_name = name;
		}

		public NffvUser EngineUser
		{
			get
			{
				return _engineUser;
			}
		}

		public Bitmap Image
		{
			get
			{
				return _image;
			}
		}

		public int ID
		{
			get
			{
				return _engineUser.Id;
			}
		}

		public string Name
		{
			get
			{
				return _name;
			}
			set
			{
				_name = value;
			}
		}

		public override string ToString()
		{
			return Name;
		}

		#region IDisposable Members

		public void Dispose()
		{
			if (_image != null)
			{
				_image.Dispose();
				_image = null;
			}
		}

		#endregion
	}
}
