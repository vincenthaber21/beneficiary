// ScannerListForm.h : header file
//

#include <Nffv/Nffv.h>
#include "afxwin.h"

#if !defined(AFX_CHECKLISTBOXCBNDLG_H__ADB1995A_6CE0_4686_B6B3_1FE2B12E1B89__INCLUDED_)
#define AFX_CHECKLISTBOXCBNDLG_H__ADB1995A_6CE0_4686_B6B3_1FE2B12E1B89__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

/////////////////////////////////////////////////////////////////////////////
// CScannerListForm dialog

class CScannerListForm : public CDialog
{
// Construction
public:
	CScannerListForm(CWnd* pParent = NULL);	// standard constructor
	~CScannerListForm();	// standard destructor

// Dialog Data
	//{{AFX_DATA(CScannerListForm)
	enum { IDD = IDD_SELECT_SCANNER_DIALOG };
	//}}AFX_DATA
	CCheckListBox	m_ctlCheckList;

	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CScannerListForm)
protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV support
	virtual BOOL OnInitDialog();	
	//}}AFX_VIRTUAL

// Implementation
protected:
	HICON m_hIcon;
	CString m_strSelectedModules;
	CString m_strFingerprintDB;
	CString m_strFingerprintDBPassword;
	CString m_strUserDB;

	CString SaveSelectedModules();

	// Generated message map functions
	//{{AFX_MSG(CScannerListForm)
	virtual void OnOK();
	afx_msg void OnSysCommand(UINT nID, LPARAM lParam);
	afx_msg void OnBnClickedOk();

	CEdit m_ctlFingerDB;
	CEdit m_ctlDBPassword;
	CEdit m_ctlUserDB;

	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
public:
	CString GetSelectedModules();
	CString GetFingerprintDB();
	CString GetFingerprintDBPassword();
	CString GetUserDB();
};

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_CHECKLISTBOXCBNDLG_H__ADB1995A_6CE0_4686_B6B3_1FE2B12E1B89__INCLUDED_)
