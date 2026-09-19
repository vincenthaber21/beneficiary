// CBusyForm.cpp : implementation file
//

#include "stdafx.h"
#include "BusyForm.h"
#include <math.h>

// CBusyForm dialog

IMPLEMENT_DYNAMIC(CBusyForm, CDialog)

CBusyForm::CBusyForm(CString description, CWnd* pParent)
	: CDialog(CBusyForm::IDD, pParent)
{
	m_description.SetString(description);
}

CBusyForm::~CBusyForm()
{
}

void CBusyForm::Stop()
{
	PostMessage(WM_CLOSE,0,0);
}

void CBusyForm::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	DDX_Control(pDX, IDC_DESCRIPTION, m_lblDescription);
}

BOOL CBusyForm::OnInitDialog()
{
	BOOL result = CDialog::OnInitDialog();
	m_lblDescription.SetWindowText(m_description);

	return result;
}

BEGIN_MESSAGE_MAP(CBusyForm, CDialog)
	ON_BN_CLICKED(IDC_SCAN_CANCEL, &CBusyForm::OnBnScanClickedCancel)
END_MESSAGE_MAP()

// CBusyForm message handlers

void CBusyForm::OnBnScanClickedCancel()
{
	CButton *pCancel = (CButton*)GetDlgItem(IDC_SCAN_CANCEL);
	pCancel->EnableWindow(FALSE);
	pCancel->RedrawWindow();

	CWnd *pParent = GetParent();
	if (pParent)
	{
		pParent->PostMessage(WM_COMMAND, MAKEWPARAM(IDC_SCAN_CANCEL, 0), 0);
	}
}
