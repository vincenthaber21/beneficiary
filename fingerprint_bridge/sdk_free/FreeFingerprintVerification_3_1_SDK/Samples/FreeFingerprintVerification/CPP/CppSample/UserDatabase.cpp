#include "stdafx.h"
#include "UserDatabase.h"
#include <fstream>

CUserDatabase::CUserDatabase(CString dbFilename)
{
	m_dbFilename = dbFilename;

	Load();
}

CUserDatabase::~CUserDatabase(void)
{
}

int CUserDatabase::GetUserCount()
{
	return (int)m_vecUserNames.size();
}

CString CUserDatabase::GetUser(int index)
{
	return m_vecUserNames.at(index);
}

void CUserDatabase::AddUserName(CString userName)
{
	m_vecUserNames.push_back(userName);
	Save();
}

void CUserDatabase::RemoveUserName(int index)
{
	std::vector<CString>::iterator iter;
	int i;
	for(iter = m_vecUserNames.begin(), i = 0; iter != m_vecUserNames.end() && i < index; iter++, i++)
	{
		continue;
	}

	if(iter != m_vecUserNames.end())
	{
		m_vecUserNames.erase(iter);
	}
	Save();
}

void CUserDatabase::ClearAllUserNames()
{
	m_vecUserNames.clear();
	Save();
}

void CUserDatabase::Save()
{
	SaveAs(m_dbFilename);
}

void CUserDatabase::SaveAs(CString dbFilename)
{
#ifdef _UNICODE
	std::wofstream fout(dbFilename);
#else
	std::ofstream fout(dbFilename);
#endif

	std::vector<CString>::iterator iter;
	for(iter = m_vecUserNames.begin(); iter != m_vecUserNames.end(); iter++)
	{
		fout << iter->GetString() << std::endl;
	}

	fout.close();
}

void CUserDatabase::Load()
{
	int MAX_LENGTH = 100;
	TCHAR line[100];
#ifdef _UNICODE
	std::wifstream fin(m_dbFilename); 
#else
	std::ifstream fin(m_dbFilename);
#endif // _UNICODE

	m_vecUserNames.clear();
	while(fin.getline(line, 100)) {
		CString name(line);
		if(name.GetLength() > 0)
		{
			AddUserName(name);
		}
	}

	fin.close();
}
