// UserPreviewForm.cpp : implementation file
//

#include "stdafx.h"
#include "UserPreviewForm.h"
#include "Nffv/NError.h"

// CUserPreviewForm dialog

IMPLEMENT_DYNAMIC(CUserPreviewForm, CDialog)

CUserPreviewForm::CUserPreviewForm(HNffvUser hUser, CWnd* pParent /*=NULL*/)
	: CDialog(CUserPreviewForm::IDD, pParent)
{
	m_hUser = hUser;
}

CUserPreviewForm::~CUserPreviewForm()
{
}

void CUserPreviewForm::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	DDX_Control(pDX, IDC_PREVIEW, m_ctlUserPreview);
}

BOOL CUserPreviewForm::OnInitDialog()
{
	BOOL initResult = CDialog::OnInitDialog();

	HBITMAP hBitmap;
	NResult result = NffvUserGetHBitmap(m_hUser, (NHandle *) &hBitmap);
	if(NFailed(result)) throw result;
	m_ctlUserPreview.SetBitmap(hBitmap);

	return initResult;
}

BEGIN_MESSAGE_MAP(CUserPreviewForm, CDialog)
END_MESSAGE_MAP()

// CUserPreviewForm message handlers
