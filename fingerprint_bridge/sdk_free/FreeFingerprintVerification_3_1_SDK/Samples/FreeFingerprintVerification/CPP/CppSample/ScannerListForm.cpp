// ScannerListForm.cpp : implementation file
//

#include "stdafx.h"
#include "CppSampleApp.h"
#include "ScannerListForm.h"
#include "Nffv/Nffv.h"
#include "Nffv/NError.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#undef THIS_FILE
static char THIS_FILE[] = __FILE__;
#endif

/////////////////////////////////////////////////////////////////////////////
// CAboutDlg dialog used for App About

class CAboutDlg : public CDialog
{
public:
	CAboutDlg();

// Dialog Data
	//{{AFX_DATA(CAboutDlg)
	enum { IDD = IDD_ABOUTBOX };
	//}}AFX_DATA

	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CAboutDlg)
	protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV support
	//}}AFX_VIRTUAL

// Implementation
protected:
	//{{AFX_MSG(CAboutDlg)
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};

CAboutDlg::CAboutDlg() : CDialog(CAboutDlg::IDD)
{
	//{{AFX_DATA_INIT(CAboutDlg)
	//}}AFX_DATA_INIT
}

void CAboutDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	//{{AFX_DATA_MAP(CAboutDlg)
	//}}AFX_DATA_MAP
}

BEGIN_MESSAGE_MAP(CAboutDlg, CDialog)
	//{{AFX_MSG_MAP(CAboutDlg)
		// No message handlers
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// CScannerListForm dialog

CScannerListForm::CScannerListForm(CWnd* pParent /*=NULL*/)
	: CDialog(CScannerListForm::IDD, pParent)
{
	//{{AFX_DATA_INIT(CScannerListForm)
		// NOTE: the ClassWizard will add member initialization here
	//}}AFX_DATA_INIT
	// Note that LoadIcon does not require a subsequent DestroyIcon in Win32
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);
}

CScannerListForm::~CScannerListForm()
{
}

void CScannerListForm::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	//{{AFX_DATA_MAP(CScannerListForm)
	//}}AFX_DATA_MAP
	DDX_Control(pDX, IDC_LIST1, m_ctlCheckList);
	DDX_Control(pDX, IDC_EDIT1, m_ctlFingerDB);
	DDX_Control(pDX, IDC_EDIT2, m_ctlDBPassword);
	DDX_Control(pDX, IDC_EDIT3, m_ctlUserDB);
}

BEGIN_MESSAGE_MAP(CScannerListForm, CDialog)
	//{{AFX_MSG_MAP(CScannerListForm)
	ON_WM_SYSCOMMAND()
	ON_WM_QUERYDRAGICON()
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// CScannerListForm message handlers

BOOL CScannerListForm::OnInitDialog()
{
	NResult result = N_OK;
	NChar * szModules = NULL;
	NInt i = 0;

	CDialog::OnInitDialog();

	// Add "About..." menu item to system menu.

	// IDM_ABOUTBOX must be in the system command range.
	ASSERT((IDM_ABOUTBOX & 0xFFF0) == IDM_ABOUTBOX);
	ASSERT(IDM_ABOUTBOX < 0xF000);

	CMenu* pSysMenu = GetSystemMenu(FALSE);
	if (pSysMenu != NULL)
	{
		CString strAboutMenu;
		strAboutMenu.LoadString(IDS_ABOUTBOX);
		if (!strAboutMenu.IsEmpty())
		{
			pSysMenu->AppendMenu(MF_SEPARATOR);
			pSysMenu->AppendMenu(MF_STRING, IDM_ABOUTBOX, strAboutMenu);
		}
	}

	// Set the icon for this dialog.  The framework does this automatically
	//  when the application's main window is not a dialog
	SetIcon(m_hIcon, TRUE);			// Set big icon
	SetIcon(m_hIcon, FALSE);		// Set small icon

	m_ctlCheckList.SetCheckStyle(BS_AUTOCHECKBOX);
	m_ctlCheckList.ResetContent();

	result = NffvGetAvailableScannerModules(&szModules);
	if(NFailed(result)) return FALSE;

	const TCHAR *separators = _T(";");
	TCHAR *token = _tcstok(szModules, separators);
	while (token != NULL)
	{
		m_ctlCheckList.AddString(token);
		m_ctlCheckList.SetCheck(i, 0);

		token = _tcstok(NULL, separators);
	}
	NffvFreeMemory(szModules);

	if (m_ctlCheckList.GetCount() == 0)
	{
		m_ctlCheckList.AddString(_T("No scanners found."));
		m_ctlCheckList.EnableWindow(FALSE);
	}

	m_ctlFingerDB.SetWindowText(_T("FingerprintDB.CppSample.dat"));
	m_ctlUserDB.SetWindowText(_T("UserDB.CppSample.txt"));

	return TRUE;  // return TRUE  unless you set the focus to a control
}

void CScannerListForm::OnOK()
{
	m_strSelectedModules = SaveSelectedModules();
	m_ctlFingerDB.GetWindowText(m_strFingerprintDB);
	m_ctlDBPassword.GetWindowText(m_strFingerprintDBPassword);
	m_ctlUserDB.GetWindowText(m_strUserDB);

	if(m_strSelectedModules.GetLength() > 0
		|| !m_ctlCheckList.IsWindowEnabled())
	{
		EndDialog(IDOK);
	}
	else
	{
		MessageBox(_T("No scanners were selected."), _T("Warning"), MB_OK | MB_ICONWARNING);
	}
}

CString CScannerListForm::SaveSelectedModules()
{
	CString strSelectedModules;
	for(int i = 0; i < m_ctlCheckList.GetCount(); i++)
	{
		if(m_ctlCheckList.GetCheck(i))
		{
			CString strModuleName;
			m_ctlCheckList.GetText(i, strModuleName);
			if (strSelectedModules.GetLength() > 0)
			{
				strSelectedModules.AppendChar(_T(';'));
			}
			strSelectedModules.Append(strModuleName);
		}
	}

	return strSelectedModules;
}

void CScannerListForm::OnSysCommand(UINT nID, LPARAM lParam)
{
	if ((nID & 0xFFF0) == IDM_ABOUTBOX)
	{
		CAboutDlg dlgAbout;
		dlgAbout.DoModal();
	}
	else
	{
		CDialog::OnSysCommand(nID, lParam);
	}
}

CString CScannerListForm::GetSelectedModules()
{
	return m_strSelectedModules;
}

CString CScannerListForm::GetFingerprintDB()
{
	return m_strFingerprintDB;
}

CString CScannerListForm::GetFingerprintDBPassword()
{
	return m_strFingerprintDBPassword;
}

CString CScannerListForm::GetUserDB()
{
	return m_strUserDB;
}
