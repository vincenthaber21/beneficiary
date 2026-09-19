// MainForm.cpp : implementation file
//

#include "stdafx.h"
#include <afxwin.h>
#include "CppSampleApp.h"
#include "MainForm.h"
#include "Resource.h"
#include "EnrollForm.h"
#include "BusyForm.h"
#include "SettingsForm.h"
#include "UserPreviewForm.h"
#include "Nffv/NError.h"

#define WM_BUSY_FORM_FINISH (WM_USER + 1001)

// CMainForm dialog

IMPLEMENT_DYNAMIC(CMainForm, CDialog)

CMainForm::CMainForm(CString & userDatabase, CWnd* pParent /*=NULL*/): 
	CDialog(CMainForm::IDD, pParent), 
	m_dbUserDatabase(userDatabase)
{
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);

	m_iEnrollTimeout = 5000;
	m_iVerifyTimeout = 2000;
}

CMainForm::~CMainForm()
{
	m_dbUserDatabase.Save();
}

void CMainForm::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	DDX_Control(pDX, IDC_PICTUREBOX, m_PictureBox);
	DDX_Control(pDX, IDC_ENROLL_BUTTON, m_btnEnroll);
	DDX_Control(pDX, IDC_USER_LIST, m_ctlUserList);
}

BOOL CMainForm::OnInitDialog()
{
	BOOL result = CDialog::OnInitDialog();

	// Set the icon for this dialog.  The framework does this automatically
	//  when the application's main window is not a dialog
	SetIcon(m_hIcon, TRUE);			// Set big icon
	SetIcon(m_hIcon, FALSE);		// Set small icon

	int count = m_dbUserDatabase.GetUserCount();

	m_ctlUserList.ResetContent();

	for(int i = 0; i < count; i++)
	{
		m_ctlUserList.AddString(m_dbUserDatabase.GetUser(i));
	}

	if (m_ctlUserList.GetCount() > 0)
	{
		m_ctlUserList.SetCurSel(0);
	}

	return result;
}

BEGIN_MESSAGE_MAP(CMainForm, CDialog)
	ON_BN_CLICKED(IDC_ENROLL_BUTTON, &CMainForm::OnBnClickedEnrollButton)
	ON_BN_CLICKED(IDC_VERIFY_BUTTON, &CMainForm::OnBnClickedVerifyButton)
	ON_COMMAND(IDC_SCAN_CANCEL, &CMainForm::OnCancelScan)
	ON_BN_CLICKED(IDC_REMOVE_USER, &CMainForm::OnBnClickedRemoveUser)
	ON_BN_CLICKED(IDC_CLEAR_DATABASE, &CMainForm::OnBnClickedClearDatabase)
	ON_BN_CLICKED(IDC_SETTINGS, &CMainForm::OnBnClickedSettings)
	ON_LBN_DBLCLK(IDC_USER_LIST, &CMainForm::OnLbnDblclkUserList)
	ON_LBN_SELCHANGE(IDC_USER_LIST, &CMainForm::onLbnMsclkUserList)
	ON_MESSAGE(WM_BUSY_FORM_FINISH, OnBusyFormFinish)
END_MESSAGE_MAP()

// CMainForm message handlers

struct EnrollParam
{
	HNffvUser * pHUser;
	CMainForm * pMainForm;
	CBusyForm * pBusyForm;
	NffvStatus engineStatus;
};

struct VerifyParam
{
	HNffvUser hUser;
	NInt * pScore;
	CMainForm * pMainForm;
	CBusyForm * pBusyForm;
	NffvStatus engineStatus;
};

UINT CMainForm::EnrollUserThread(LPVOID pParam)
{
	EnrollParam *pEnrollParam = (EnrollParam*)pParam;
	CMainForm* form = (CMainForm*)pEnrollParam->pMainForm;

	NResult result = NffvEnroll(form->m_iEnrollTimeout, &pEnrollParam->engineStatus, pEnrollParam->pHUser);
	if(NFailed(result)) throw result;

	form->PostMessage(WM_BUSY_FORM_FINISH, 0, (LPARAM)pEnrollParam->pBusyForm);

	return 0;   // thread completed successfully
}

UINT CMainForm::VerifyUserThread(LPVOID pParam)
{
	VerifyParam *pVerifyParam = (VerifyParam*)pParam;
	CMainForm* form = ((CMainForm*)pVerifyParam->pMainForm);

	NResult result = NffvVerify(pVerifyParam->hUser, 20000, &pVerifyParam->engineStatus, pVerifyParam->pScore);
	if(NFailed(result)) throw result;

	form->PostMessage(WM_BUSY_FORM_FINISH, 0, (LPARAM)pVerifyParam->pBusyForm);

	return 0;   // thread completed successfully
}

void CMainForm::OnBnClickedClearDatabase()
{
	if (::AfxMessageBox(_T("Do you really want to remove all users?"), MB_YESNO | MB_ICONQUESTION) != IDYES)
	{
		return;
	}

	m_dbUserDatabase.ClearAllUserNames();
	m_ctlUserList.ResetContent();
	NResult result = NffvClearUsers();
	if(NFailed(result)) throw result;
}

void CMainForm::OnBnClickedVerifyButton()
{
	NResult result;
	HNffvUser hUser;
	NInt score;	
	CBusyForm busy("Waiting for fingerprint...");

	int i;
	for(i = 0; i < m_ctlUserList.GetCount(); i++)
	{
		if(m_ctlUserList.GetSel(i) == 1)
		{
			break;
		}
	}

	if(i < m_ctlUserList.GetCount())
	{
		result = NffvGetUser(i, &hUser);
		if(NFailed(result)) throw result;

		VerifyParam p;
		p.pMainForm = this;
		p.pBusyForm = &busy;
		p.hUser = hUser;
		p.pScore = &score;
		
		AfxBeginThread(VerifyUserThread, &p);
		busy.DoModal();

		if (p.engineStatus == nfesTemplateCreated)
		{
			if (score > 0)
			{
				HBITMAP hBitmap;
				result = NffvUserGetHBitmap(hUser, (NHandle*) &hBitmap);
				if(NFailed(result)) throw result;
				m_PictureBox.SetBitmap(hBitmap);

				CString userName;
				m_ctlUserList.GetText(i, userName);
				CString msg;
				msg.Format(_T("%s verified.\r\n")
					_T("Fingerprints match. Score: %d"),
					userName.GetString(), score);

				MessageBox(msg.GetString(), _T("Fingerprints verification"));
			}
			else
			{
				MessageBox(_T("Fingerprints did not match"), _T("Fingerprints verification"));
			}
		}
		else
		{
			CString description = GetNffvStatusDescription(p.engineStatus);
			CString errorMsg;
			errorMsg.Format(_T("Verification failed. Reason: %s"), description);
			MessageBox(errorMsg);
		}
	}
	else if(m_ctlUserList.GetCount() > 0)
	{
		MessageBox(_T("Please select user from user list to be verified."), _T("Note"), MB_ICONINFORMATION);
	}
	else
	{
		MessageBox(_T("Please enroll user to verify."), _T("Note"), MB_ICONINFORMATION);
	}
}

void CMainForm::OnBnClickedEnrollButton()
{
	HNffvUser hUser;
	NResult result;
	NInt count;
	CBusyForm busy("Waiting for fingerprint...");

	result = NffvGetUserCount(&count);
	if(NFailed(result)) throw result;

	if(count >= NFFV_MAX_USER_COUNT)
	{
		MessageBox(_T("Maximum number of users is reached."), _T("Info"), MB_ICONEXCLAMATION);
	}
	else
	{
		EnrollParam p;
		p.pMainForm = this;
		p.pHUser = &hUser;
		p.pBusyForm = &busy;
		
		CEnrollForm dlg;
		long long res = dlg.DoModal();
		if(res == IDOK)
		{
			AfxBeginThread(EnrollUserThread, &p);
			busy.DoModal();

			if(p.engineStatus == nfesTemplateCreated)
			{
				HBITMAP hBitmap;
				result = NffvUserGetHBitmap(hUser, (NHandle*) &hBitmap);
				if(NFailed(result)) throw result;
				m_PictureBox.SetBitmap(hBitmap);

				m_ctlUserList.InsertString(-1, dlg.GetUser());
				m_dbUserDatabase.AddUserName(dlg.GetUser());
				m_ctlUserList.SetCurSel(m_ctlUserList.GetCount() - 1);
			}
			else
			{
				CString description = GetNffvStatusDescription(p.engineStatus);
				CString errorMsg;
				errorMsg.Format(_T("Enrollment failed. Reason: %s"), description);
				MessageBox(errorMsg);
			}
		}
	}
}

LRESULT CMainForm::OnBusyFormFinish(WPARAM wParam, LPARAM lParam)
{
	CBusyForm *busyForm = (CBusyForm*)lParam;
	busyForm->Stop();
	return 0;
}

void CMainForm::OnCancelScan()
{
	NffvCancel();
}

void CMainForm::OnBnClickedRemoveUser()
{
	if (::AfxMessageBox(_T("Do you really want to remove selected user?"), MB_YESNO | MB_ICONQUESTION) != IDYES)
	{
		return;
	}

	NResult result;
	BOOL selected = FALSE;

	int i;
	for(i = 0; i < m_ctlUserList.GetCount(); i++)
	{
		if(m_ctlUserList.GetSel(i) == 1)
		{
			selected = TRUE;
			break;
		}
	}

	if(selected)
	{
		result = NffvRemoveUser(i);
		if(NFailed(result)) throw result;

		m_ctlUserList.DeleteString(i);
		m_dbUserDatabase.RemoveUserName(i);

		if (i < m_ctlUserList.GetCount())
		{
			m_ctlUserList.SetCurSel(i);
		}
		else if (m_ctlUserList.GetCount() > 0)
		{
			m_ctlUserList.SetCurSel(m_ctlUserList.GetCount() - 1);
		}
	}
}

int CMainForm::GetSelectedUserIndex()
{	
	for(int i = 0; i < m_ctlUserList.GetCount(); i++)
	{
		if(m_ctlUserList.GetSel(i) == 1)
		{
			return i;
		}
	}
	return -1;
}

void CMainForm::OnBnClickedSettings()
{
	CSettingsForm settings;

	long long result = settings.DoModal();
}

void CMainForm::OnLbnDblclkUserList()
{
	int selected = GetSelectedUserIndex();
	HNffvUser hUser;
	NResult result;

	if(selected != -1)
	{
		result = NffvGetUser(selected, &hUser);
		if(NFailed(result)) throw result;

		CUserPreviewForm preview(hUser);
		preview.DoModal();
	}
}

void CMainForm::onLbnMsclkUserList()
{
	int selected = GetSelectedUserIndex();
	HNffvUser hUser;
	NResult result;
	HBITMAP hBitmap;

	if (selected != -1)
	{
		result = NffvGetUser(selected, &hUser);
		if (NFailed(result)) throw result;
		result = NffvUserGetHBitmap(hUser, (NHandle*)&hBitmap);
		if (NFailed(result)) throw result;

		m_PictureBox.SetBitmap(hBitmap);
	}
}

const TCHAR* CMainForm::GetNffvStatusDescription(NffvStatus status)
{
	switch (status)
	{
	case nfesNone: return _T("None");
	case nfesTemplateCreated: return _T("Template created");
	case nfesNoScanner: return _T("No scanner");
	case nfesScannerTimeout: return _T("Scanner timeout");
	case nfesUserCanceled: return _T("User cancelled.");
	case nfesQualityCheckFailed: return _T("Quality check failed");
	default: return _T("");
	}
}
