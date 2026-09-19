#pragma once
#include "afxwin.h"
#include "resource.h"
#include <Nffv/Nffv.h>

// CUserPreviewForm dialog

class CUserPreviewForm : public CDialog
{
	DECLARE_DYNAMIC(CUserPreviewForm)

public:
	CUserPreviewForm(HNffvUser hUser, CWnd* pParent = NULL);   // standard constructor
	virtual ~CUserPreviewForm();

// Dialog Data
	enum { IDD = IDD_PRIEVIEW_FORM };

protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV support
	virtual BOOL OnInitDialog();

	HNffvUser m_hUser;

	DECLARE_MESSAGE_MAP()
public:
	CStatic m_ctlUserPreview;
};
