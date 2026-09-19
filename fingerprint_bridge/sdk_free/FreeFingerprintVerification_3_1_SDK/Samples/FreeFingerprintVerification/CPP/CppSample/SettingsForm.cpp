// SettingsForm.cpp : implementation file
//

#include "stdafx.h"
#include "SettingsForm.h"
#include "Nffv/NError.h"

#include <iostream>
#include <math.h>
#include <limits>
#include <tchar.h>
#include <wchar.h>

// CSettingsForm dialog

IMPLEMENT_DYNAMIC(CSettingsForm, CDialog)

CSettingsForm::CSettingsForm(CWnd* pParent /*=NULL*/)
	: CDialog(CSettingsForm::IDD, pParent)
{
}

CSettingsForm::~CSettingsForm()
{
}

void CSettingsForm::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	DDX_Control(pDX, IDC_MATCHING_THRESHOLD, m_ctlMatchingThresholdList);
	DDX_Control(pDX, IDC_EDIT2, m_ctlQualityThreshold);
}

BOOL CSettingsForm::OnInitDialog()
{
	BOOL result = CDialog::OnInitDialog();

	NInt threshold;
	NByte quality;

	result = NffvGetQualityThreshold(&quality);
	if(NFailed(result)) throw result;
	result = NffvGetMatchingThreshold(&threshold);
	if(NFailed(result)) throw result;

	CString qualityString;
	qualityString.Format(_T("%d"), quality);
	m_ctlQualityThreshold.SetWindowText(qualityString);

	CString matchingThreshold = MatchingThresholdToString(threshold);

	m_ctlMatchingThresholdList.AddString(_T("0.1%"));
	m_ctlMatchingThresholdList.AddString(_T("0.01%"));
	m_ctlMatchingThresholdList.AddString(_T("0.001%"));

	m_ctlMatchingThresholdList.SelectString(-1, matchingThreshold);

	return result;
}

CString CSettingsForm::MatchingThresholdToString(int value)
{
	CString strValue, format;
	double p = -value / 12.0;
	double c = ceil(-p);
	format.Format(_T("%%.%df%%%%"), (int) max(0, c - 2));
	strValue.Format(format, pow(10, p + 2));
	
	return strValue;
}

int CSettingsForm::MatchingThresholdFromString(CString & value)
{
	float matchingThresholdPercent = 0;
	#undef min
	double epsylon = std::numeric_limits<double>::min(); 
	#define min(a, b) (((a) < (b)) ? (a) : (b))

	CString str(value);

	str.Remove(_T('%'));
	str.Replace(_T(','), _T('.'));

	_stscanf_s(str, _T("%f"), &matchingThresholdPercent);

	return max(0, (int) (-12 * log10(max(epsylon, min(1 , matchingThresholdPercent / 100)))));
}
	
void CSettingsForm::OnOK()
{
	CString strMatchingThreshold;
	CString strQualityThreshold;
	double matchingThresholdPercent = 0;
	int qualityThreshold = 100, matchingThreshold = 0;
	NResult result;

	m_ctlQualityThreshold.GetWindowText(strQualityThreshold);
	if (_stscanf_s(strQualityThreshold, _T("%d"), &qualityThreshold) != 1
		|| qualityThreshold < 0
		|| qualityThreshold > 255)
	{
		AfxMessageBox(_T("Quality threshold must be from 0 to 255."));
		return;
	}

	int nIndex = m_ctlMatchingThresholdList.GetCurSel();
	if (nIndex != CB_ERR)
	{
		m_ctlMatchingThresholdList.GetLBText(nIndex, strMatchingThreshold);
		matchingThreshold = MatchingThresholdFromString(strMatchingThreshold);
	}
	else
	{
		AfxMessageBox(_T("Invalid matching threshold."));
		return;
	}

	result = NffvSetMatchingThreshold(matchingThreshold);
	if(NFailed(result)) throw result;

	result = NffvSetQualityThreshold(qualityThreshold);
	if(NFailed(result)) throw result;

	CDialog::OnOK();
}

BEGIN_MESSAGE_MAP(CSettingsForm, CDialog)
END_MESSAGE_MAP()

// CSettingsForm message handlers
