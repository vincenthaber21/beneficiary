// ScannerList.cpp : Defines the class behaviors for the application.
//

#include "stdafx.h"
#include "CppSampleApp.h"
#include "ScannerListForm.h"
#include "Nffv/NError.h"
#include "Nffv/Nffv.h"
#include "MainForm.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#undef THIS_FILE
static char THIS_FILE[] = __FILE__;
#endif

/////////////////////////////////////////////////////////////////////////////
// CCppSampleApp

BEGIN_MESSAGE_MAP(CCppSampleApp, CWinApp)
	//{{AFX_MSG_MAP(CCppSampleApp)
		// NOTE - the ClassWizard will add and remove mapping macros here.
		//    DO NOT EDIT what you see in these blocks of generated code!
	//}}AFX_MSG
	ON_COMMAND(ID_HELP, CWinApp::OnHelp)
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// CCppSampleApp construction

CCppSampleApp::CCppSampleApp()
{
	// TODO: add construction code here,
	// Place all significant initialization in InitInstance
}

/////////////////////////////////////////////////////////////////////////////
// The one and only CCppSampleApp object

CCppSampleApp theApp;

/////////////////////////////////////////////////////////////////////////////
// CCppSampleApp initialization

BOOL CCppSampleApp::InitInstance()
{
	NResult result;
	AfxEnableControlContainer();

	// Standard initialization
	// If you are not using these features and wish to reduce the size
	//  of your final executable, you should remove from the following
	//  the specific initialization routines you do not need.

#ifdef _AFXDLL
	//Enable3dControls();			// Call this when using MFC in a shared DLL
#else
	//Enable3dControlsStatic();	// Call this when linking to MFC statically
#endif

	CScannerListForm dlg;

	try
	{
		//m_pMainWnd = &dlg;
		int nResponse = dlg.DoModal();
		
		if (nResponse == IDOK)
		{
			CString strModules(dlg.GetSelectedModules());
			CString strFingerprintDB(dlg.GetFingerprintDB());
			CString strFingerprintDBPassword(dlg.GetFingerprintDBPassword());
			CString strUserDB(dlg.GetUserDB());

			result = NffvInitialize((NWChar*)strFingerprintDB.GetString(), (NWChar*)strFingerprintDBPassword.GetString(), (NWChar*)strModules.GetString());
			if(NFailed(result))
			{
				AfxMessageBox(_T("Failed to initialize Nffv or create/load database.\r\n")
					_T("Please check if:\r\n")
					_T(" - Provided password is correct;\r\n")
					_T(" - Database filename is correct;\r\n")
					_T(" - Scanners are used properly.\r\n"), MB_OK | MB_ICONERROR);
				return FALSE;
			}

			CMainForm mainForm(strUserDB);
			mainForm.DoModal();

			NffvUninitialize();
		}
	}
	catch(NResult res)
	{
		NChar szError[256];
		NffvGetErrorMessage(res, szError);

		MessageBox(0, CString(szError), _T("Error"), MB_ICONERROR | MB_OK);
	}

	// Since the dialog has been closed, return FALSE so that we exit the
	//  application, rather than start the application's message pump.
	return FALSE;
}
