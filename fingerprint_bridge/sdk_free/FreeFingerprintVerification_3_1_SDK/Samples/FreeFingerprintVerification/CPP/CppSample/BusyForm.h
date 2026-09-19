#pragma once
#include "Resource.h"
#include "afxcmn.h"
#include "afxwin.h"

// CBusyForm dialog

class CBusyForm : public CDialog
{
	DECLARE_DYNAMIC(CBusyForm)

public:
	CBusyForm(CString description, CWnd* pParent = NULL);   // standard constructor
	virtual ~CBusyForm();
	void Stop();

// Dialog Data
	enum { IDD = IDD_BUSY };

protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV support
	virtual BOOL OnInitDialog();

	CStatic m_lblDescription;
	CString m_description;

	DECLARE_MESSAGE_MAP()
public:
	afx_msg void OnBnScanClickedCancel();
};
