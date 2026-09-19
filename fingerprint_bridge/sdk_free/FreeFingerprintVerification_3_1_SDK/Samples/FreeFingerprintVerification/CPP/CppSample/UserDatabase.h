#pragma once

#include <vector>

class CUserDatabase
{
public:
	CUserDatabase(CString dbFilename);
	~CUserDatabase(void);

	int GetUserCount();
	CString GetUser(int index);
	void AddUserName(CString userName);
	void RemoveUserName(int index);
	void ClearAllUserNames();
	void Save();
	void SaveAs(CString dbFilename);

private:
	CString m_dbFilename;	
	std::vector<CString> m_vecUserNames;
	
	void Load();
};
