Attribute VB_Name = "������������"
Option Explicit

' ���� Token ���ͣ����ڴ洢������Ĺ�ʽԪ��
Type Token
   symbol As String  ' ���ţ���������"f1"���������"+"��
   Flag As Boolean   ' ����Ƿ�Ϊ���� (True) �������/���� (False)
   VarIndex As Integer ' ����Ǳ������洢����ԭʼ�����б��е����� (��1��ʼ)
End Type

' ���������ı��ʽ�ṹ
Type ParsExpression
   Count As Integer      ' Token ������
   Tokens() As Token   ' �洢�������� Token ����
End Type

' ���嵥�������������
Type CalDataItemSetup
   ItemName As String    ' �¼����������
   Id As String          ' �¼������Ψһ��ʶ (ͨ���� "f" + ���)
   ParamSeq As Integer   ' �¼���������չ������б��е��������
   CalFormula As String  ' �û������ԭʼ���㹫ʽ�ַ���
   Unit As Variant       ' ��λ
   SL As Variant         ' �������
   SU As Variant         ' �������
   Expression As ParsExpression ' ������Ĺ�ʽ�ṹ
End Type

' �������м��������õļ���
Type CalDataItemSetupInfo
   Count As Integer          ' �����������
   Rule() As CalDataItemSetup ' �洢���м��������õ�����
End Type

' ���������� TestInfo ����ӻ������в����������������
Public Function AddCalData(TestInfo As CPLot)
   Dim mySetupInfo As CalDataItemSetupInfo
   mySetupInfo = ReadSetupInfo() ' �����ñ��ȡ�������
   If mySetupInfo.Count = 0 Then Exit Function ' ���û�ж������������˳�
   
   ' ��չ TestInfo �ṹ�������µļ�������
   ExtendDataSize TestInfo, mySetupInfo
   ' ���� TestInfo �еĲ��������Ϣ (Params ����)
   UpdateSpec TestInfo, mySetupInfo
   ' ����ÿ�� Wafer�����㲢����µ�����
   UpdateData TestInfo, mySetupInfo
End Function

' ��չ TestInfo ���ݽṹ�Ĵ�С�԰����µļ������
Private Function ExtendDataSize(TestInfo As CPLot, mySetupInfo As CalDataItemSetupInfo)
   Dim OriginalParamCount: OriginalParamCount = TestInfo.ParamCount
   Dim TotalCount: TotalCount = mySetupInfo.Count + OriginalParamCount
   With TestInfo
      .ParamCount = TotalCount
      ReDim Preserve .Params(1 To TotalCount) ' ��չ�����������
      Dim i: For i = 1 To .WaferCount
         .Wafers(i).ParamCount = TotalCount
         ReDim Preserve .Wafers(i).ChipDatas(1 To TotalCount) ' ��չÿ�� Wafer �����ݴ洢����
         ' Ϊ�²���Ԥ����ռ� (������)
         Dim NewParamIndex: For NewParamIndex = 1 To mySetupInfo.Count
            Dim x: ReDim x(1 To .Wafers(i).ChipCount, 1 To 1)
            .Wafers(i).ChipDatas(OriginalParamCount + NewParamIndex) = x
         Next
      Next
   End With
End Function

' ���� TestInfo �е� Params ���飬����¼�����Ĺ����Ϣ
Private Function UpdateSpec(TestInfo As CPLot, mySetupInfo As CalDataItemSetupInfo)
   Dim i: For i = 1 To mySetupInfo.Count
      AddNewSpecInfo TestInfo, mySetupInfo.Rule(i)
   Next
End Function

' �������� Wafer�����ü��㺯������ÿ�� Wafer ����������
Private Function UpdateData(TestInfo As CPLot, mySetupInfo As CalDataItemSetupInfo)
   With mySetupInfo
      Dim i: For i = 1 To .Count
         UpdateWaferData TestInfo, .Rule(i)
      Next
   End With
End Function

' �������¼�����Ĺ����Ϣ��ӵ� TestInfo.Params ������
Private Function AddNewSpecInfo(TestInfo As CPLot, myRule As CalDataItemSetup)
   With myRule
      Dim myParamSeq: myParamSeq = .ParamSeq ' ��ȡ�²������������
   End With
   With TestInfo.Params(myParamSeq)
      .DisplayName = myRule.ItemName
      .Id = myRule.Id  ' ʹ�������е� ItemName ��Ϊ ID ���ܸ���������ǰ���� fN
      .SL = myRule.SL
      .SU = myRule.SU
      .Unit = myRule.Unit
      ReDim .TestCond(1 To 1)
      .TestCond(1) = myRule.CalFormula ' ��ԭʼ��ʽ���� TestCond
   End With
End Function

' ����ָ�� Wafer ���¼�������
Private Function UpdateWaferData(TestInfo As CPLot, myRule As CalDataItemSetup)
   With TestInfo
      Dim i: For i = 1 To .WaferCount
         CalNewData .Wafers(i).ChipDatas, myRule
      Next
   End With
End Function

' ���ļ��㺯�������ݽ�����Ĺ�ʽ (myRule.Expression) ���������� (ChipDatas)�������²�����ֵ
Private Function CalNewData(ChipDatas() As Variant, myRule As CalDataItemSetup)
' ����ÿ�� Chip (ÿһ������)
Dim Row: For Row = LBound(ChipDatas(1)) To UBound(ChipDatas(1))
   With myRule
      Dim myParamSeq: myParamSeq = .ParamSeq ' �²�����Ŀ��������
      Dim CalExpression As String: CalExpression = "" ' ���ڹ����� Evaluate �ı��ʽ�ַ���
      Dim CalFlag As Boolean: CalFlag = True ' ��ǵ�ǰ�еļ����Ƿ���Ч�������������Ƿ񶼴��ڣ�
      
      ' ����������Ĺ�ʽ Tokens
      With .Expression
         Dim i: For i = 1 To .Count
            With .Tokens(i)
               If .Flag Then ' ����Ǳ��� (�� f1)
                  Dim v: v = ChipDatas(.VarIndex)(Row, 1) ' �� ChipDatas ��ȡ��Ӧ������ֵ
                  ' ��������ı���ֵ��Ч (Error �� Empty)�����Ǽ�����Ч������ѭ��
                  If IsError(v) Then CalFlag = False: Exit For
                  If IsEmpty(v) Then CalFlag = False: Exit For
                  ' ���⴦��ȷ�� Evaluate ��������ȷ����С��1��С�� (VBA Evaluate ��һ��Ǳ������)
                  'If v < 1 And v > 0 And v <> 0 Then v = "0" & v
                  CalExpression = CalExpression & CStr(v) ' ������ֵƴ�ӵ����ʽ�ַ���
               Else ' ��������������
                  CalExpression = CalExpression & .symbol ' ֱ�ӽ�����ƴ�ӵ����ʽ�ַ���
               End If
            End With
         Next
      End With
      
      ' ���������Ч (�����������ݶ�����)
      If CalFlag Then
         On Error Resume Next ' ��ʱ���� Evaluate ���ܲ����Ĵ��� (�����)
         Dim Result: Result = Application.Evaluate(CalExpression) ' ʹ�� Excel �� Evaluate ִ�м���
         If Err.Number = 0 Then ' ��� Evaluate û�г���
             If IsNumeric(Result) Then ' ȷ���������ֵ����
                ChipDatas(myParamSeq)(Row, 1) = Result ' ������������Ŀ����
             Else
                 ' ����ѡ���¼������ÿ�
                 ChipDatas(myParamSeq)(Row, 1) = CVErr(xlErrNA) ' ���Ϊ #N/A
             End If
         Else
            ChipDatas(myParamSeq)(Row, 1) = CVErr(xlErrValue) ' Evaluate �������Ϊ #VALUE!
         End If
         On Error GoTo 0 ' �ָ�������
      Else
         ChipDatas(myParamSeq)(Row, 1) = CVErr(xlErrNA) ' ��������ȱʧ�����Ϊ #N/A
      End If
   End With
Next
End Function

' �� CAL_DATA_SETUP_SHEET �������ȡ�������������Ϣ
Public Function ReadSetupInfo() As CalDataItemSetupInfo
   Dim Ret As CalDataItemSetupInfo
   On Error Resume Next
   Dim ws As Worksheet: Set ws = CAL_DATA_SETUP_SHEET
   If Err.Number <> 0 Then
       gShow.ErrStop "��ȡ������������ʧ��", OCAP:="��ȷ�� 'Sheet1' (CAL_DATA_SETUP_SHEET) �����Ұ�����ȷ�����á�"
       Exit Function
   End If
   On Error GoTo 0
   
   Dim x: x = ws.Range("a1").CurrentRegion.Value
   If Not IsArray(x) Then Exit Function ' �����ȡʧ�ܻ�����Ϊ��
   If UBound(x, 2) < 2 Then Exit Function ' ����Ҫ�����ƺ�ID��
   
   Dim i As Long: For i = 2 To UBound(x, 2)
      ' �������У����㹫ʽ���Ƿ�ǿգ���Ϊ��Ч����ı�־
      If x(3, i) <> "" Then
         With Ret
            .Count = .Count + 1
            ReDim Preserve .Rule(1 To .Count)
            .Rule(.Count) = CreateCalDataItemSetup(x, i)
         End With
      End If
   Next
   ReadSetupInfo = Ret
End Function

' ���ݴӹ������ȡ������ x �������� i���������� CalDataItemSetup �ṹ
Private Function CreateCalDataItemSetup(x, i) As CalDataItemSetup
   Dim Ret As CalDataItemSetup
   With Ret
      .ItemName = x(1, i) ' ��һ�У���Ŀ����
      .Id = x(2, i)       ' �ڶ��У���ĿID (��ʽӦΪ fN)
      .ParamSeq = SplitVarIndex(.Id) ' �� ID (fN) ��ȡ��� N ��Ϊ�������
      .CalFormula = x(3, i) ' �����У����㹫ʽ
      .Expression = ParseFormula(.CalFormula) ' ������ʽ�ַ���Ϊ Token �ṹ
      .Unit = x(4, i)     ' �����У���λ
      .SL = x(5, i)       ' �����У��������
      .SU = x(6, i)       ' �����У��������
   End With
   CreateCalDataItemSetup = Ret
End Function

' ������ʽ�ַ��� (myFormula)������ֽ�Ϊ Token ���飬�洢�� ParsExpression �ṹ��
' ���������ʽΪ fN (NΪ����)
Private Function ParseFormula(myFormula As String) As ParsExpression
   Dim Ret As ParsExpression
   Dim Start As Long: Start = 1
   Dim State As String ' ״̬��״̬: "" (��ʼ/�����), "Var" (����)
   Dim Group As String ' ��ǰ�ַ�������: "f", "d" (����), "else" (����)
   Dim Index As Long
   
   For Index = 1 To Len(myFormula)
      Dim s As String: s = Mid(myFormula, Index, 1)
      Select Case LCase(s) ' ���Դ�Сд
      Case "f"
         If State <> "Var" Then ' ���֮ǰ���Ǳ���״̬
            ' �� f ֮ǰ�ķǱ������֣������/���������Ϊ Token
            If Start < Index Then AddToken Ret, CreateToken(myFormula, Start, Index - 1, False)
            State = "Var" ' �������״̬
            Start = Index ' ��¼������ʼλ��
         Else ' ���֮ǰ�Ѿ��Ǳ���״̬ (�����ϲ�Ӧ���� ff)
             ' �����ǹ�ʽ��������򵥴�������֮ǰ�ı�������ʼ�µ� f
            AddToken Ret, CreateToken(myFormula, Start, Index - 1, True) ' �����ɱ���
            Start = Index ' ��ʼ�±����������Ǵ���ģ�
            State = "Var"
         End If
         Group = "f"
      Case "0" To "9"
         If State = "Var" Then
             Group = "d" ' �ڱ���״̬���������֣����Ϊ������
         Else ' ���ڱ���״̬����������
             If Group <> "d" And Start < Index Then ' ���ǰ�治�����֣��������ݣ����ǰ������ݼ�ΪToken
                 AddToken Ret, CreateToken(myFormula, Start, Index - 1, False)
                 Start = Index
             End If
             Group = "d" ' ���Ϊ�����飨��Ϊ������һ���֣�
         End If
      Case Else ' �����ַ� (�����, ���ŵ�)
         If State = "Var" Then ' ���֮ǰ�Ǳ���״̬
            ' ���������������� (fN) ���Ϊ Token
            AddToken Ret, CreateToken(myFormula, Start, Index - 1, True)
            State = "" ' �˳�����״̬
            Start = Index ' ��¼��ǰ�����/���ŵĿ�ʼλ��
         Else ' ���֮ǰ���Ǳ���״̬
             If Start < Index Then ' ��֮ǰ�������/�������Ϊ Token
                AddToken Ret, CreateToken(myFormula, Start, Index - 1, False)
             End If
             Start = Index ' ��¼��ǰ�����/���ŵĿ�ʼλ��
         End If
         Group = "else"
      End Select
   Next
   
   ' ����ʽĩβʣ��Ĳ���
   AddToken Ret, CreateToken(myFormula, Start, Len(myFormula), State = "Var")
   
   ParseFormula = Ret
End Function

' ���´����� Token ��ӵ� ParsExpression �ṹ�� Tokens ������
Private Function AddToken(Ret As ParsExpression, newToken As Token)
   With Ret
      .Count = .Count + 1
      ReDim Preserve .Tokens(1 To .Count)
      .Tokens(.Count) = newToken
   End With
End Function

' ���ݹ�ʽƬ�δ��� Token �ṹ
Private Function CreateToken(myFormula As String, Start, Finish, VarFlag As Boolean) As Token
   Dim Ret As Token
   With Ret
      .Flag = VarFlag ' ����Ƿ�Ϊ����
      .symbol = Mid(myFormula, Start, Finish - Start + 1) ' ��ȡ�����ַ���
      If .Flag Then ' ����Ǳ��� (fN)
         .VarIndex = SplitVarIndex(.symbol) ' �ӷ�������ȡ�������� N
      End If
   End With
   CreateToken = Ret
End Function

' �ӱ������� (�� "f12") ����ȡ�������� (12)
Private Function SplitVarIndex(symbol) As Integer
   On Error Resume Next ' ��ֹ Val �Է����ֲ��ֱ���
   SplitVarIndex = Val(Mid(symbol, 2)) ' �ӵڶ����ַ���ʼȡֵ
   On Error GoTo 0
End Function

' ������Ӽ������ݵ������Ƿ���ȷ
Public Function SetupCheck_ADD_CAL_DATA(TestInfo As CPLot) As Boolean
   Dim SetupOk As Boolean: SetupOk = True ' Ĭ������Ϊ True
   Dim r As CalDataItemSetupInfo: r = ReadSetupInfo()
   If r.Count = 0 Then SetupCheck_ADD_CAL_DATA = True: Exit Function ' û����������ΪOK
   
   Dim OriginalParamCount As Integer: OriginalParamCount = TestInfo.ParamCount
   
   With r
      Dim i: For i = 1 To .Count
         ' ������ ID (fN) �е���� N �Ƿ���� ԭʼ�������� + ��ǰ������� i
         If .Rule(i).ParamSeq <> OriginalParamCount + i Then
            gShow.ErrAlarm Array("������Ŀ����ĵ�" & i & "��:", _
                                 .Rule(i).Id, _
                                 "������˳����ȷ", _
                                 "Ԥ��IDӦΪ f" & OriginalParamCount + i)
            SetupOk = False ' ������ô���
         End If
         
         ' ��鹫ʽ��ʹ�õı����Ƿ���Ч
         With .Rule(i).Expression
            Dim j: For j = 1 To .Count
               If .Tokens(j).Flag Then ' ֻ������ Token
                  Dim VarIdx As Integer: VarIdx = .Tokens(j).VarIndex
                  ' ���������������ԭʼ��������
                  If VarIdx > OriginalParamCount Then
                      ' �����������Ƿ��Ǳ��μ�����ǰ���Ѷ����ĳ���±���
                     If IsNewVarNameExists(.Tokens(j).symbol, r, i) = False Then
                        gShow.ErrAlarm Array("������Ŀ�����м�����ʽ���ڴ���:", _
                                             "��ʽ: " & r.Rule(i).CalFormula, _
                                             "��Ŀ: " & r.Rule(i).Id,
                                             "ʹ����δ����ı���: " & .Tokens(j).symbol)
                        SetupOk = False ' ������ô���
                     End If
                  End If
               End If
            Next
         End With
      Next
   End With
   SetupCheck_ADD_CAL_DATA = SetupOk
End Function

' ���һ�������� (toCheckName, �� fN) �Ƿ����ڵ�ǰ������ (CurItemIndex) ֮ǰ�����ĳ���¼������ ID
Private Function IsNewVarNameExists(toCheckName, r As CalDataItemSetupInfo, CurItemIndex) As Boolean
   Dim Ret As Boolean: Ret = False
   With r
       ' ֻ��鵱ǰ��֮ǰ�Ĺ���
      Dim i: For i = 1 To CurItemIndex - 1
         If LCase(.Rule(i).Id) = LCase(toCheckName) Then ' �Ƚ� ID (���Դ�Сд)
            Ret = True: Exit For
         End If
      Next
   End With
   IsNewVarNameExists = Ret
End Function
