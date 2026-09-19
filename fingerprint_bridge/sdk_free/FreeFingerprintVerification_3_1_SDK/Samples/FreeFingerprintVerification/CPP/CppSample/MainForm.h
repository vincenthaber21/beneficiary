#pragma once
#include "afxwin.h"
#include <Nffv/Nffv.h>
#include "UserDatabase.h"

// CMainForm dialog

class CMainForm : public CDialog
{
	DECLARE_DYNAMIC(CMainForm)

public:
	CMainForm(CString & userDatabase, CWnd* pParent = NULL);   // standard constructor
	virtual ~CMainForm();

// Dialog Data
	enum { IDD = IDD_MAIN_FORM };

protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV support
	virtual BOOL OnInitDialog();

	HICON m_hIcon;
	CUserDatabase m_dbUserDatabase;

	DECLARE_MESSAGE_MAP()

private:
	int m_iEnrollTimeout;
	int m_iVerifyTimeout;

	CStatic m_PictureBox;
	CButton m_btnEnroll;

	afx_msg void OnBnClickedEnrollButton();
	afx_msg void OnBnClickedVerifyButton();
	afx_msg void OnCancelScan();
	afx_msg void OnBnClickedRemoveUser();
	afx_msg void OnBnClickedClearDatabase();
	afx_msg LRESULT OnBusyFormFinish(WPARAM, LPARAM);

	int GetSelectedUserIndex();

	CStatic m_pbox;
	CListBox m_ctlUserList;
	void SetUserDatabase(CString filename);
	void SetFingerprintDatabase(CString filename);
	afx_msg void OnBnClickedSettings();
	afx_msg void OnLbnDblclkUserList();
	afx_msg void onLbnMsclkUserList();

	static const TCHAR* GetNffvStatusDescription(NffvStatus status);

	static UINT EnrollUserThread(LPVOID pParam);
	static UINT VerifyUserThread(LPVOID pParam);
};
