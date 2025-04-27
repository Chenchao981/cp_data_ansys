Attribute VB_Name = "DCP��ʽ���ݲɼ�"
Option Explicit

' ����DCP��ʽ�����ļ����к��г���
Const PARAM_START_COL As Integer = 5  ' ������ʼ��
Const STD_ITEM_ROW As Long = 7       ' ��׼��Ŀ��
Const USER_ITEM_ROW As Long = 7      ' �û���Ŀ��
Const UPPER_ROW As Long = 8          ' ������
Const LOWER_ROW As Long = 9          ' ������
Const COND_START_ROW As Long = 10    ' ����������ʼ��
Const COND_END_ROW As Long = 15      ' ��������������

Const DATA_START_ROW As Integer = 16 ' ���ݿ�ʼ��
Const SEQ_COL As Integer = 1         ' �����
Const X_COL As Integer = 2           ' X������
Const Y_COL As Integer = 3           ' Y������
Const BIN_COL As Integer = 4         ' Bin��

Dim ParamPos() As Integer '������Ϊ�������,����Ϊ��������

' ��鲢ȷ����6��Ϊ���У�������������һ������
Public Sub CheckSixthRow(WaferDataSheet As Worksheet)
   With WaferDataSheet
      If .Cells(6, 1) <> "" Then
         .Rows(6).Insert  ' �ڵ�6�в���һ������
      End If
   End With
End Sub

' ��DCP��ʽ�ļ�����ȡ��Ϣ��TestInfo����
Function SplitInfo_DCP(TestInfo As CPLot, WaferDataSheet As Worksheet, WaferIndex)
   CheckSixthRow WaferDataSheet  ' ȷ����6��Ϊ����
   With TestInfo
      If .ParamCount = 0 Then AddParamInfo TestInfo, WaferDataSheet, ParamPos  ' ����ǵ�һƬ����Ӳ�����Ϣ
      AddWaferInfo .Wafers(WaferIndex), WaferDataSheet, .ParamCount  ' ��Ӿ�Բ��Ϣ
   End With
End Function

' ��Ӳ�����Ϣ
Private Function AddParamInfo(ByRef LotInfo As CPLot, WaferDataSheet As Worksheet, ByRef ParamPos() As Integer)
   Dim WaferData: WaferData = WaferDataSheet.UsedRange.Value
   Dim myParams() As TestItem
   Dim ParamIndex As Integer
   Dim myPos() As Integer: ReDim myPos(1 To UBound(WaferData, 2))
   Dim ColIndex As Integer: For ColIndex = PARAM_START_COL To UBound(WaferData, 2)
      If WaferData(USER_ITEM_ROW, ColIndex) <> "Dischage Time" Then  ' ����"Dischage Time"
         ParamIndex = ParamIndex + 1
         myPos(ColIndex) = ParamIndex
         ReDim Preserve myParams(1 To ParamIndex)
         With myParams(ParamIndex)
            .DisplayName = WaferData(USER_ITEM_ROW, ColIndex)  ' ������ʾ����
            .Group = WaferData(USER_ITEM_ROW, ColIndex)        ' ��������
            Dim TestNameDic As Object
            .Id = Change2UniqueName(.Group, TestNameDic)       ' ת��ΪΨһ����
            .Unit = SplitUnit(WaferData(LOWER_ROW, ColIndex))  ' ��ȡ��λ
            .SL = ChangeVal(WaferData(LOWER_ROW, ColIndex))    ' ��������
            .SU = ChangeVal(WaferData(UPPER_ROW, ColIndex))    ' ��������
            ReDim .TestCond(1 To COND_END_ROW - COND_START_ROW + 1)
            Dim i: For i = 1 To COND_END_ROW - COND_START_ROW + 1
               .TestCond(i) = WaferData(COND_START_ROW + i - 1, ColIndex)  ' ���ò�������
            Next
         End With
      End If
   Next
   
   ParamPos = myPos
   With LotInfo
      .ParamCount = ParamIndex
      .Params = myParams
      .Product = Replace(WaferData(1, 2), ".dcp", "")  ' ���ò�Ʒ����ȥ��.dcp��׺
   End With
End Function

' ���ݵ�λת��ֵ
Private Function ChangeVal(spec)
   Dim Ret
   With RegEx
      Ret = Val(spec) * CalRate(.LastSubMatchValue("\d+(\.\d+)?([munpfk]?)(?:V|A|OHM)", spec))  ' ʹ��������ʽ��ȡ��λ�����㻻����
   End With
   ChangeVal = Ret
End Function

' ���㵥λ������
Private Function CalRate(RateStr)
   Dim Ret
   Select Case LCase(RateStr)
   Case "m"
      Ret = 0.001          ' �� (milli)
   Case "u"
      Ret = 0.000001       ' ΢ (micro)
   Case "n"
      Ret = 0.000000001    ' �� (nano)
   Case "p"
      Ret = 0.000000000001 ' Ƥ (pico)
   Case "f"
      Ret = 0.000000000000001 ' �� (femto)
   Case "k"
      Ret = 1000           ' ǧ (kilo)
   Case Else
      Ret = 1              ' �޵�λǰ׺
   End Select
   CalRate = Ret
End Function

' �ӹ���ַ�������ȡ��λ
Private Function SplitUnit(spec) As String
   Dim Ret As String
   With RegEx
      Ret = .LastSubMatchValue("\d+(\.\d+)?[munpfk]?(V|A|OHM)", spec)  ' ʹ��������ʽ��ȡ��λ
   End With
   SplitUnit = Ret
End Function

' ��Ӿ�Բ��Ϣ
Private Function AddWaferInfo(WaferInfo As CPWafer, _
                              WaferDataSheet As Worksheet, _
                              ParamCount As Integer)
   Dim DataCount As Long: DataCount = WaferDataSheet.UsedRange.Rows.Count - DATA_START_ROW + 1  ' �������ݵ�����
   With WaferInfo
      .WaferId = WaferDataSheet.Cells(3, 2).Value  ' ���þ�ԲID
      .Seq = GetList(WaferDataSheet, SEQ_COL, DATA_START_ROW, DataCount)  ' ��ȡ����б�
      .Bin = GetList(WaferDataSheet, BIN_COL, DATA_START_ROW, DataCount)  ' ��ȡBinֵ�б�
      .x = GetList(WaferDataSheet, X_COL, DATA_START_ROW, DataCount)      ' ��ȡX�����б�
      .Y = GetList(WaferDataSheet, Y_COL, DATA_START_ROW, DataCount)      ' ��ȡY�����б�
      .Width = WorksheetFunction.Max(.x) - WorksheetFunction.Min(.x) + 2  ' ���㾧Բ���
      ReDim .ChipDatas(1 To ParamCount)
      Dim i As Integer: For i = LBound(ParamPos) To UBound(ParamPos)
         If ParamPos(i) > 0 Then
            .ChipDatas(ParamPos(i)) = GetList(WaferDataSheet, i, DATA_START_ROW, DataCount)  ' ��ȡоƬ����
         End If
      Next
      .ParamCount = ParamCount
      .ChipCount = DataCount
   End With
End Function




