#pragma once
#include "afxwin.h"
#include "Resource.h"

// CEnrollForm dialog

class CEnrollForm : public CDialog
{
	DECLARE_DYNAMIC(CEnrollForm)

public:
	CEnrollForm(CWnd* pParent = NULL);   // standard constructor
	virtual ~CEnrollForm();
	CString GetUser();

// Dialog Data
	enum { IDD = IDD_ENROLL_DIALOG };

protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV support
	virtual void OnOK();
	virtual BOOL OnInitDialog();

	CString m_userName;

	DECLARE_MESSAGE_MAP()

public:
	CEdit m_ctlUserNameEdit;
};
