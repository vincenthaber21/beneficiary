// EnrollForm.cpp : implementation file
//

#include "stdafx.h"
#include "EnrollForm.h"

// CEnrollForm dialog

IMPLEMENT_DYNAMIC(CEnrollForm, CDialog)

CEnrollForm::CEnrollForm(CWnd* pParent /*=NULL*/)
	: CDialog(CEnrollForm::IDD, pParent)
{
}

CEnrollForm::~CEnrollForm()
{
}

void CEnrollForm::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	DDX_Text(pDX, IDC_USER_NAME_EDIT, m_userName);
	if (pDX->m_bSaveAndValidate)
	{
		if (m_userName.Trim().GetLength() == 0)
		{
			pDX->Fail();
		}
	}
}

void CEnrollForm::OnOK()
{
	if (UpdateData(TRUE))
	{
		EndDialog(1);
	}
	else
	{
		MessageBox(_T("Entered ID is not allowed."), _T("Warning"));
	}
}

BOOL CEnrollForm::OnInitDialog()
{
	BOOL result = CDialog::OnInitDialog();
	return result;
}

CString CEnrollForm::GetUser()
{
	return m_userName;
}

BEGIN_MESSAGE_MAP(CEnrollForm, CDialog)
END_MESSAGE_MAP()

// CEnrollForm message handlers
