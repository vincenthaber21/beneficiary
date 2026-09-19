#pragma once

#include "resource.h"

#include <Nffv/Nffv.h>
#include "afxwin.h"

// CSettingsForm dialog

class CSettingsForm : public CDialog
{
	DECLARE_DYNAMIC(CSettingsForm)

public:
	CSettingsForm(CWnd* pParent = NULL);   // standard constructor
	virtual ~CSettingsForm();

// Dialog Data
	enum { IDD = IDD_SETTINGS };

protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV support
	virtual BOOL OnInitDialog();
	virtual void OnOK();

	CString MatchingThresholdToString(int value);
	int MatchingThresholdFromString(CString & value);

	DECLARE_MESSAGE_MAP()
public:
	CComboBox m_ctlMatchingThresholdList;
	CEdit m_ctlQualityThreshold;
};
