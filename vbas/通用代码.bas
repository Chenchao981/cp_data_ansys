Attribute VB_Name = "ͨ�ô���"
Option Explicit

' �� Tab �ָ�����ʽ���ı��ļ�
Public Function OpenTabTextxlDelimitedFile(fName) As Workbook
   On Error Resume Next ' ���Կ��ܵĴ򿪴���
   Workbooks.OpenText Filename:=fName, _
      Origin:=1251, StartRow:=1, DataType:=xlDelimited, Tab:=True, _
      FieldInfo:=Array(Array(1, 1), Array(2, 1)), TrailingMinusNumbers:=True ' Origin 1251 ��Ӧ Windows ANSI (Cyrillic)
   If Err.Number <> 0 Then
       gShow.ErrAlarm "���ļ�ʧ��: " & fName & vbCrLf & Err.Description
       Set OpenTabTextxlDelimitedFile = Nothing
   Else
       Set OpenTabTextxlDelimitedFile = ActiveWorkbook
   End If
   On Error GoTo 0
End Function

' �����ļ�ѡ��Ի������û�ѡ���ļ�
' FileDescription: �Ի�������ʾ���ļ���������
' MultiSelect: �Ƿ������ѡ
' ExtendName: �ɱ�������飬����������ļ���չ�� (�����㣬�� "txt", "csv")
Public Function PickupFile(FileDescription, MultiSelect As Boolean, ParamArray ExtendName())
   Dim Ret
   Dim f As String, p: p = ExtendName
   f = CreateFileFilter(p) ' �����ļ��������ַ���
   Dim tmpFiles
   tmpFiles = Application.GetOpenFilename(FileFilter:=FileDescription & " (" & f & ")," & f, _
                                    Title:="ѡ��" & FileDescription, MultiSelect:=MultiSelect)
   
   ' ����û��Ƿ�ȡ����ѡ��
   If VarType(tmpFiles) = vbBoolean Then Exit Function
   
   If MultiSelect Then
      ' ��������ѡ��GetOpenFilename ����һ�������ļ�·��������
      QuickSort tmpFiles ' ��ѡ����ļ��б�������� (���ļ���)
      Ret = tmpFiles
   Else
      ' ���ֻ����ѡ��GetOpenFilename ����һ���ַ���
      ' �����װ�ɵ�Ԫ�����飬�Ա��ַ�������һ��
      ReDim Ret(1 To 1)
      Ret(1) = tmpFiles
   End If
   PickupFile = Ret
End Function

' ������չ���б��� GetOpenFilename ��Ҫ���ļ��������ַ���
' ���磬���� ("xls", "xlsx") ���� "*.xls;*.xlsx"
Private Function CreateFileFilter(ExtendNameList) As String
   Dim Ret As String
   Dim x: x = ExtendNameList
   Dim i: For i = LBound(ExtendNameList) To UBound(ExtendNameList)
      x(i) = "*." & x(i) ' Ϊÿ����չ����� "*."
   Next
   Ret = Join(x, ";") ' �÷ֺ�����
   CreateFileFilter = Ret
End Function

' ��������п������� (����)
Public Sub QuickSort(ByRef x)
    Dim iLBound As Long
    Dim iUBound As Long
    Dim iTemp
    Dim iOuter As Long
    Dim iMax As Long
  
    iLBound = LBound(x)
    iUBound = UBound(x)
  
    ' �������ֻ��һ��Ԫ�ػ�Ϊ�գ�����������
    If (iUBound <= iLBound) Then Exit Sub
    
    ' �����ֵ�Ƶ�ĩβ (��������ƺ����Ǳ�׼���������һ���֣�������ĳ���Ż����ض�����?)
    ' ��׼��������ͨ��ѡ���һ�������һ�����м�Ԫ����Ϊ��׼
    iMax = iLBound
    For iOuter = iLBound + 1 To iUBound
        If x(iOuter) > x(iMax) Then iMax = iOuter
    Next iOuter
    iTemp = x(iMax)
    x(iMax) = x(iUBound)
    x(iUBound) = iTemp
  
    ' ��ʼ��׼�Ŀ�������ݹ����
    InnerQuickSort x, iLBound, iUBound - 1 ' �Գ������һ��(���ֵ)֮��Ĳ��ֽ�������
End Sub

' ����������ڲ��ݹ麯��
Private Sub InnerQuickSort(ByRef x, ByVal iLeftEnd As Long, ByVal iRightEnd As Long)
    Dim iLeftCur As Long
    Dim iRightCur As Long
    Dim iPivot
    Dim iTemp
  
    ' �ݹ���ֹ����
    If iLeftEnd >= iRightEnd Then Exit Sub
  
    ' ѡ���һ��Ԫ����Ϊ��׼ (Pivot)
    iLeftCur = iLeftEnd
    iRightCur = iRightEnd + 1
    iPivot = x(iLeftEnd)
  
    Do
        ' �������Ҳ��ҵ�һ�����ڵ��ڻ�׼��Ԫ��
        Do
            iLeftCur = iLeftCur + 1
            If iLeftCur > iRightEnd Then Exit Do ' ��ֹԽ��
        Loop While x(iLeftCur) < iPivot
       
        ' ����������ҵ�һ��С�ڵ��ڻ�׼��Ԫ��
        Do
            iRightCur = iRightCur - 1
            If iRightCur < iLeftEnd Then Exit Do ' ��ֹԽ��
        Loop While x(iRightCur) > iPivot
       
        ' �������ָ�뽻�棬���ַ�������
        If iLeftCur >= iRightCur Then Exit Do
       
        ' ��������ָ��ָ���Ԫ��
        iTemp = x(iLeftCur)
        x(iLeftCur) = x(iRightCur)
        x(iRightCur) = iTemp
    Loop
  
    ' ����׼Ԫ�طŵ���ȷ��λ�� (iRightCur ָ���λ��)
    x(iLeftEnd) = x(iRightCur)
    x(iRightCur) = iPivot
  
    ' �Ի�׼�������ߵ���������еݹ�����
    InnerQuickSort x, iLeftEnd, iRightCur - 1
    InnerQuickSort x, iRightCur + 1, iRightEnd
End Sub

' ȷ������Ψһ�ԡ���� toCheckName �� NameDic ���Ѵ��ڣ�����ĩβ������ֺ�׺ (2, 3, ...) ֱ��Ψһ
' NameDic: һ�� Scripting.Dictionary �������ڴ洢��ʹ�õ�����
Public Function Change2UniqueName(toCheckName As String, NameDic As Object) As String
   Dim Ret As String: Ret = toCheckName
   ' ��� NameDic δ��ʼ�����򴴽��µ��ֵ����
   If NameDic Is Nothing Then Set NameDic = CreateObject("scripting.dictionary")
   Dim k As Integer: k = 1
   Do While NameDic.exists(Ret)
      k = k + 1
      Ret = toCheckName & k
   Loop
   NameDic.Add Ret, 1 ' �������ɵ�Ψһ������ӵ��ֵ���
   Change2UniqueName = Ret
End Function

' ���ַ�������ȡ��һ���ض��ַ���Χ������
' ����: SplitContentInPairChar("abc[xyz]def", "[]") ���� "xyz"
Public Function SplitContentInPairChar(toSplitInfo, Optional PairChar = "[]") As String
   If Len(PairChar) < 2 Then Exit Function ' �����ṩһ���ַ�
   Dim Ret As String
   Dim LeftChar As String: LeftChar = Left(PairChar, 1)
   Dim RightChar As String: RightChar = Right(PairChar, 1) ' ������Ӧȡ���һ���ַ�
   
   Dim PosLeft As Long: PosLeft = InStr(1, toSplitInfo, LeftChar)
   Dim PosRight As Long: PosRight = InStrRev(toSplitInfo, RightChar)
   
   If PosLeft > 0 And PosRight > PosLeft Then
       Ret = Mid(toSplitInfo, PosLeft + 1, PosRight - PosLeft - 1)
   End If

   SplitContentInPairChar = Ret
End Function

' ����һ���µ� Excel ���������������ṩ�������б� (SheetNames) ����������
' SheetNames: ����������򶺺ŷָ����ַ���
Public Function CreateResultBook(Optional SheetNames) As Workbook
   Dim SheetNameList: SheetNameList = CheckList(SheetNames) ' �������������ȷ��������
   Dim ww As Workbook
   Dim AdjustNewSheetNumFlag As Boolean: AdjustNewSheetNumFlag = IsArray(SheetNameList)
   Dim OldSheetNum As Integer
   
   On Error Resume Next ' ���Կ��ܵĴ���
   If AdjustNewSheetNumFlag And IsArrayNotEmpty(SheetNameList) Then
      Dim NewSheetNum As Integer: NewSheetNum = UBound(SheetNameList) - LBound(SheetNameList) + 1
      If NewSheetNum > 0 Then
          OldSheetNum = Application.SheetsInNewWorkbook
          Application.SheetsInNewWorkbook = NewSheetNum ' ��ʱ�����½�������ʱ��Ĭ�Ϲ���������
      Else
          AdjustNewSheetNumFlag = False ' ��������б�Ϊ�գ���Ĭ�����ô���
      End If
   End If
   
   Set ww = Workbooks.Add ' �����¹�����
   
   If AdjustNewSheetNumFlag Then
      Application.SheetsInNewWorkbook = OldSheetNum ' �ָ�Ĭ������
      If Not ww Is Nothing Then ' ȷ���������ѳɹ�����
         With ww
            Dim Index As Integer: Index = LBound(SheetNameList)
            Dim j As Integer: For j = 1 To .Worksheets.Count
               If Index <= UBound(SheetNameList) Then
                   .Worksheets(j).Name = SheetNameList(Index)
                   Index = Index + 1
               Else
                   ' ����ṩ����������ʵ�ʴ����Ĺ����������ɾ������Ļ���Ĭ������
                   ' Application.DisplayAlerts = False
                   ' .Worksheets(j).Delete
                   ' Application.DisplayAlerts = True
               End If
            Next
         End With
      End If
   End If
   On Error GoTo 0 ' �ָ�������
   
   Set CreateResultBook = ww
End Function

' �ӹ������л�ȡָ���С�ָ����ʼ�к����������ݷ�Χ (Range ����)
Public Function GetList(WaferDataSheet As Worksheet, _
                         SpecificCol As Integer, _
                         StartRow As Long, DataCount As Long) As Range
   Dim Ret As Range
   If DataCount <= 0 Then Exit Function ' �������Ϊ 0 ���������� Nothing
   On Error Resume Next
   Set Ret = WaferDataSheet.Cells(StartRow, SpecificCol).Resize(DataCount)
   If Err.Number <> 0 Then Set Ret = Nothing ' ��ȡ��Χ�����򷵻� Nothing
   On Error GoTo 0
   Set GetList = Ret
End Function

' ���ݵ�λǰ׺ (n, u, m, k) ��ȡ������ת���� (����ڱ�׼��λ)
Public Function GetUnitOrderChangeRate(Unit As String) As Double
   Dim Ret As Double: Ret = 1 ' Ĭ��Ϊ 1
   If Len(Unit) = 0 Then GetUnitOrderChangeRate = 1: Exit Function
   
   Select Case LCase(Left(Unit, 1))
      Case "n": Ret = 1E-09
      Case "u": Ret = 1E-06
      Case "m": Ret = 0.001
      Case "k": Ret = 1000
      Case Else: Ret = 1
   End Select
   GetUnitOrderChangeRate = Ret
End Function

' ����Ӿɵ�λ (oldUnit) ת�����µ�λ (newUnit) �ı���
Public Function GetUnitChangeRate(newUnit, oldUnit) As Double
   Dim Ret As Double
   Dim newRate As Double: newRate = GetUnitOrderChangeRate(newUnit)
   Dim oldRate As Double: oldRate = GetUnitOrderChangeRate(oldUnit)
   If oldRate = 0 Then GetUnitChangeRate = 0: Exit Function ' ����������
   Ret = newRate / oldRate
   GetUnitChangeRate = Ret
End Function

' ��һ���Ա�׼��λ��ʾ��ֵ������Ŀ�굥λ (Unit) ����ת��
Public Function ChangeWithUnit(ValueWithStdUnit, Unit As String) As Variant
   Dim Ret As Variant
   If IsEmpty(ValueWithStdUnit) Or Not IsNumeric(ValueWithStdUnit) Then
       ChangeWithUnit = ValueWithStdUnit ' ���������Ч����ԭ������
       Exit Function
   End If
   Dim Rate As Double: Rate = 1 / GetUnitOrderChangeRate(Unit) ' ����ӱ�׼��λ��Ŀ�굥λ�ĳ���
   Ret = CDbl(ValueWithStdUnit) * Rate
   ChangeWithUnit = Ret
End Function

' ʹ��ѡ����ճ���� UnitRateRng ��ֵ���� DataRng �����ֵ
' ͨ�����ڽ����������ֵ��ĳ����λ����ת��Ϊ��׼��λ����һ��λ
Public Sub ChangeRangeUnit(UnitRateRng As Range, DataRng As Range)
    On Error Resume Next
    UnitRateRng.Copy
    DataRng.PasteSpecial Paste:=xlPasteValues, Operation:=xlMultiply, SkipBlanks:=True
    Application.CutCopyMode = False ' ���������
    If Err.Number <> 0 Then
        gShow.ErrAlarm "��Χ��λת��ʧ��: " & Err.Description
    End If
    On Error GoTo 0
End Sub


' ������ı��� (info) ת��Ϊ�ַ�����������������û��з����Ӹ�Ԫ��
Function Info2Str(info) As String
   Dim Ret As String
   If IsArray(info) Then
      Dim x() As String: ReDim x(LBound(info) To UBound(info))
      Dim i: For i = LBound(info) To UBound(info)
         x(i) = Info2Str(info(i)) ' �ݹ���ô�������Ԫ��
      Next
      Ret = Join(x, vbCrLf)
   Else
      Ret = CStr(info) ' ǿ��ת��Ϊ�ַ���
   End If
   Info2Str = Ret
End Function
