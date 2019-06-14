Const ForReading = 1, ForAppending = 8
Const BIF_RETURNONLYFSDIRS = &H0001, BSR_DRIVES = 17 
'�����һ��������Ϊһ�����䣬�������ΪTrue��
'�������ΪFalse����ʾ�����еĿ�ͷ���ǿո�ʱ������һ�����䡣
Const g_bOneLine_Is_OneParagraph = True
'�ο�Emeditor��URL��ʶ�𷽷����ַ���
Const pattern_URL = "((https?:\/\/)|(ftp:\/\/)|(file:)|(mailto:))[!#%&,-:;=@_~\d\w\$\'\(\)\*\+\.\/\?\^\\]+"
Const pattern_TrimTail = "([!:;,\'\(\)\.\?]*)$"
'������������
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
Set regEx = New RegExp
regEx.IgnoreCase = True
regEx.Global = True
'�ڽű����ڵ�Ŀ¼�£������ļ�һ���ļ�����
strCurDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
g_strParaFile = strCurDir & "\File1.txt"
g_strURLFile = strCurDir & "\File2.txt"

'ѡ������Ŀ¼��
strFolder = BrowseForFolder("��ѡ������Ŀ¼", BIF_RETURNONLYFSDIRS, BSR_DRIVES)
If objFSO.FolderExists(strFolder) Then
	SearchTXTFile(objFSO.GetFolder(strFolder))
	MsgBox "������ϣ�" & vbcrlf & "������浽��ǰĿ¼�µ�File1.txt��File2.txt"
End If

'��ʾĿ¼ѡ��Ի������û�ѡ��������Ŀ¼��
Function BrowseForFolder(strTitle, uFlag, strRoot)
	On Error Resume Next
	Set objApplication = CreateObject("Shell.Application")
	Set objItem = objApplication.BrowseForFolder(&H0, strTitle, uFlag, strRoot)
	If Err <> 0 OR objItem Is Nothing Then
		BrowseForFolder = ""
	Else
		BrowseForFolder = objItem.Self.Path
	End If
	On Error GoTo 0
End Function

'����ָ��Ŀ¼���������е�TXT�ļ���
Sub SearchTXTFile(objFolder)
	'����Ŀ¼�����е�TXT�ļ���
	Set colFiles = objFolder.Files
	For Each objFile In colFiles
		If UCase(objFSO.GetExtensionName(objFile.Path)) = "TXT" Then
			ExtractURL(objFile)
		End If
	Next
	'�ݹ�������е���Ŀ¼��
	Set colSubFolders = objFolder.SubFolders
	For Each objSubFolder In colSubFolders
		SearchTXTFile(objSubFolder)
	Next
End Sub

'��TXT�ļ���ȡ��URL��
Sub ExtractURL(objFile)
	On Error Resume Next
	Set objStream = objFile.OpenAsTextStream(ForReading)
	'������ε����ݡ�
	arParagraphs = GetParagraphs(objStream.ReadAll())
	For Each strParagraph In arParagraphs
		regEx.Pattern = pattern_URL	'��������ģʽ��
		Set colURLS = regEx.Execute(strParagraph)	'���Ҷ����е�URL��
		If colURLS.Count > 0 Then
			Dump strParagraph, g_strParaFile	'������URL���ӵĶ��䱣�浽�ļ�һ��
			'��ÿ��URL���ӱ��浽�ļ�����
			For Each objURL In colURLS
				Dump TailTrim(objURL.Value), g_strURLFile
			Next
		End If
	Next
	objStream.Close()
	On Error GoTo 0
End Sub

'���ļ��ĸ������䱣�浽�����С������ԡ�g_bOneLine_Is_OneParagraph��������Ϊ�������ݡ�
Function GetParagraphs(strText)
	If g_bOneLine_Is_OneParagraph Then
		GetParagraphs = Split(strText, vbcrlf)
	Else
		GetParagraphs = Split(strText, vbcrlf & " ")
	End If
End Function

'�ο�Emeditor��URL��β����������Щ�ַ�����!'(),.:;?�������URL��β������Щ�ַ�����ɾ�����ǡ�
Function TailTrim(strURL)
	regEx.Pattern = pattern_TrimTail
	Set colMatches = regEx.Execute(strURL)
	TailTrim = Left(strURL, colMatches(0).FirstIndex)
End Function

'�����ݱ��浽�ļ���
Sub Dump(strText, strFile)
	Set objFile = objFSO.OpenTextFile(strFile, ForAppending, True)
	objFile.Write(strText & vbcrlf)
	objFile.Close()
End Sub
