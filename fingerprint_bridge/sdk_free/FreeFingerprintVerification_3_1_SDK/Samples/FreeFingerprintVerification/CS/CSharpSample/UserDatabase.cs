using System;
using System.Collections.Generic;
using System.Text;
using System.Xml.Serialization;
using System.Collections;
using System.IO;

namespace CSharpSample
{
	public class UserRecord
	{
		[XmlAttribute("id")]
		public int _id;
		[XmlAttribute("name")]
		public string _name;

		public UserRecord()
		{
			_id = 0;
			_name = string.Empty;
		}

		public UserRecord(int id, string name)
		{
			_id = id;
			_name = name;
		}

		public int ID
		{
			get
			{
				return _id;
			}
		}

		public string Name
		{
			get
			{
				return _name;
			}
		}
	}

	[XmlRoot("UserDatabase")]
	public class UserDatabase : List<UserRecord>
	{
		public void WriteToFile(string filename)
		{
			TextWriter w = null;
			try
			{
				XmlSerializer s = new XmlSerializer(typeof(UserDatabase));
				w = new StreamWriter(filename);
				s.Serialize(w, this);
				w.Close();
			}
			catch (Exception ex)
			{
				throw ex;
			}
			finally
			{
				if (w != null)
				{
					w.Close();
					w = null;
				}
			}
		}

		public static UserDatabase ReadFromFile(string filename)
		{
			UserDatabase newUserDb = null;
			TextReader r = null;
			try
			{
				XmlSerializer s = new XmlSerializer(typeof(UserDatabase));
				r = new StreamReader(filename);
				newUserDb = (UserDatabase)s.Deserialize(r);
			}
			catch (Exception ex)
			{
				throw ex;
			}
			finally
			{
				r.Close();
			}

			return newUserDb;
		}

		public UserRecord Lookup(int id)
		{
			foreach (UserRecord userRec in this)
			{
				if (userRec.ID == id)
				{
					return userRec;
				}
			}

			return null;
		}
	}
}
