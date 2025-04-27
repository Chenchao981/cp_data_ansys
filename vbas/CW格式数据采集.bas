Attribute VB_Name = "CW��ʽ���ݲɼ�"
Option Explicit

' ����CW��ʽ�����ļ����к��г���
Const PARAM_START_COL As Integer = 11      ' ����������ʼ��
Const STD_ITEM_ROW As Long = 14           ' ��׼��Ŀ��
Const USER_ITEM_ROW As Long = 15          ' �û���Ŀ��
Const LIMIT_ROW As Long = 16              ' ����ֵ��
Const COND_START_ROW As Long = 17         ' ����������ʼ��
Const COND_END_ROW As Long = 18           ' ��������������

Const UNIT_RATE_ROW As Integer = 20       ' ��λ������
Const DATA_START_ROW As Integer = 30      ' ���ݿ�ʼ��
Const SEQ_COL As Integer = 1              ' �����
Const BIN_COL As Integer = 2              ' Binֵ��
Const X_COL As Integer = 3                ' X������
Const Y_COL As Integer = 5                ' Y������

Dim ParamPos() As Integer '������Ϊ�������,����Ϊ��������

' ��CW��ʽ����Բ�ļ�����ȡ��Ϣ��TestInfo����
Public Function SplitInfo_CWSW(TestInfo As CPLot, WaferDataSheet As Worksheet, WaferIndex)
   WaferDataSheet.UsedRange.Replace What:="Untested", Replacement:="", LookAt:=xlWhole  ' �滻"Untested"Ϊ��
   With TestInfo
      If .ParamCount = 0 Then AddParamInfo TestInfo, WaferDataSheet  ' ����ǵ�һƬ����Ӳ�����Ϣ
      AddWaferInfo .Wafers(WaferIndex), WaferDataSheet, .ParamCount  ' ��Ӿ�Բ��Ϣ
   End With
End Function

' ��ȡ��һ����Ŀ����
Private Function GetNextItemName(WaferData, CurItemCol) As String
   Dim Ret As String
   Dim NextItemCol As Integer: NextItemCol = CurItemCol + 2
   If NextItemCol <= UBound(WaferData, 2) Then Ret = WaferData(USER_ITEM_ROW, NextItemCol)
   GetNextItemName = Ret
End Function

' �ж���һ����Ŀ�Ƿ�Ϊ"same"
Private Function NextItemIsSame(WaferData, CurItemCol) As Boolean
   Dim Ret As Boolean
   Dim NextItemName As String
   NextItemName = LCase(GetNextItemName(WaferData, CurItemCol))
   Ret = ("same" = NextItemName)
   NextItemIsSame = Ret
End Function

' ���ݲ������²�����������Ʒ�ʽ�����޻����ޣ�
Private Function GuessParamQC(Param) As String
   Dim Ret As String
   Ret = IIf(UCase(Left(Param, 1)) = "B", "ExceptHi", "ExceptLow")  ' �����������B��ͷ���²�Ϊ���޿��ƣ�����Ϊ���޿���
   GuessParamQC = Ret
End Function

' ���ò���������ֵ
Private Function SetupLimit(WaferData, ColIndex, Param As TestItem)
   Dim Limit: Limit = WaferData(LIMIT_ROW, ColIndex)
   With Param
      .Unit = Trim(Right(Limit, 2))  ' ��ȡ��λ
      If NextItemIsSame(WaferData, ColIndex) Then
         .SL = Val(Limit)  ' ��ǰ��Ϊ����
         .SU = Val(WaferData(LIMIT_ROW, ColIndex + 2))  ' ������Ϊ����
      Else
         If GuessParamQC(.Group) = "ExceptHi" Then
            .SL = Val(Limit)  ' �²�Ϊ���޿��ƣ���������
         Else
            .SU = Val(Limit)  ' �²�Ϊ���޿��ƣ���������
         End If
      End If
   End With
End Function

' ��Ӳ�����Ϣ
Private Function AddParamInfo(ByRef LotInfo As CPLot, WaferDataSheet As Worksheet, Optional MWFlag As Boolean = False)
   Dim WaferData: WaferData = WaferDataSheet.UsedRange.Value
   Dim myParams() As TestItem
   Dim ParamIndex As Integer
   Dim myPos() As Integer: ReDim myPos(1 To UBound(WaferData, 2))
   Dim ColIndex As Integer: For ColIndex = PARAM_START_COL To UBound(WaferData, 2)
      Dim toCheckName As String: toCheckName = WaferData(USER_ITEM_ROW, ColIndex)
      If toCheckName <> "SAME" And toCheckName <> "" Then  ' ����"SAME"�Ϳ�����
         ParamIndex = ParamIndex + 1
         myPos(ColIndex) = ParamIndex
         ReDim Preserve myParams(1 To ParamIndex)
         With myParams(ParamIndex)
            .DisplayName = WaferData(USER_ITEM_ROW, ColIndex)  ' ������ʾ����
            .Group = WaferData(USER_ITEM_ROW, ColIndex)        ' ��������
            Dim TestNameDic As Object
            .Id = Change2UniqueName(.Group, TestNameDic)       ' ת��ΪΨһ����
            SetupLimit WaferData, ColIndex, myParams(ParamIndex)  ' ��������ֵ
            ReDim .TestCond(1 To COND_END_ROW - COND_START_ROW + 1)
            Dim i: For i = 1 To COND_END_ROW - COND_START_ROW + 1
               .TestCond(i) = WaferData(COND_START_ROW + i - 1, ColIndex)  ' ���ò�������
            Next
            WaferDataSheet.Cells(UNIT_RATE_ROW, ColIndex) = ChangeWithUnit(1, .Unit)  ' ���õ�λ����
         End With
      End If
   Next
   
   ParamPos = myPos
   With LotInfo
      .ParamCount = ParamIndex
      .Params = myParams
      If MWFlag Then
         .Product = WaferDataSheet.Name  ' �ྦྷԲʱ��Ʒ��Ϊ��������
      Else
         .Product = Split(WaferDataSheet.Name, "-")(0)  ' ����Բʱ��Ʒ��Ϊ���������ĵ�һ����
      End If
   End With
End Function

' ���ļ�������ȡ��Բ���
Private Function SplitWaferNoFromFileName(tmpFileName)
   Dim Pos As Long
   Pos = InStrRev(tmpFileName, "-")
   If Pos > 0 Then
      SplitWaferNoFromFileName = Mid(tmpFileName, Pos + 1, Len(tmpFileName) - Pos - 4)
   End If
End Function

' ���ļ�������ȡ������Ϣ
Private Function SplitLot(tmpFileName)
   Dim s: s = tmpFileName
   Dim Pos As Long: Pos = InStrRev(s, "-")
   If Pos > 0 Then SplitLot = Left(s, Pos - 1)
End Function

' ��Ӿ�Բ��Ϣ
Private Function AddWaferInfo(WaferInfo As CPWafer, _
                              WaferDataSheet As Worksheet, _
                              ParamCount As Integer, _
                              Optional WaferStartRow)
   Dim myStartRow As Long
   If IsMissing(WaferStartRow) Then
      myStartRow = DATA_START_ROW  ' ʹ��Ĭ�����ݿ�ʼ��
   Else
      myStartRow = WaferStartRow   ' ʹ��ָ�������ݿ�ʼ��
   End If
   
   Dim DataCount As Long: DataCount = WaferDataSheet.Cells(myStartRow, 3)  ' ��ȡоƬ����
   Dim DataStartRow As Long: DataStartRow = myStartRow + 3  ' ʵ�����ݿ�ʼ��
   With WaferInfo
      If IsMissing(WaferStartRow) Then
         .WaferId = Right(WaferDataSheet.Name, 2)  ' ����Բʱ���ӹ�������������ȡ��ԲID
      Else
         .WaferId = WaferDataSheet.Cells(myStartRow, 2)  ' �ྦྷԲʱ���ӵ�Ԫ���ȡ��ԲID
      End If
      .Seq = GetList(WaferDataSheet, SEQ_COL, DataStartRow, DataCount)  ' ��ȡ����б�
      .Bin = GetList(WaferDataSheet, BIN_COL, DataStartRow, DataCount)  ' ��ȡBinֵ�б�
      .x = GetList(WaferDataSheet, X_COL, DataStartRow, DataCount)      ' ��ȡX�����б�
      .Y = GetList(WaferDataSheet, Y_COL, DataStartRow, DataCount)      ' ��ȡY�����б�
      .Width = WorksheetFunction.Max(.x) - WorksheetFunction.Min(.x) + 2  ' ���㾧Բ���
      ReDim .ChipDatas(1 To ParamCount)
      Dim i As Integer: For i = LBound(ParamPos) To UBound(ParamPos)
         If ParamPos(i) > 0 Then
            Dim UnitRateCell As Range
            Set UnitRateCell = WaferDataSheet.Cells(UNIT_RATE_ROW, i)
            UnitRateCell = ChangeWithUnit(1, Right(WaferDataSheet.Cells(LIMIT_ROW, i), 2))  ' ���õ�λ����
            Dim ChipDataRng As Range
            Set ChipDataRng = GetList(WaferDataSheet, i, DataStartRow, DataCount)
            ChangeRangeUnit UnitRateCell, ChipDataRng  ' Ӧ�õ�λ����
            .ChipDatas(ParamPos(i)) = ChipDataRng.Value  ' �洢оƬ����
         End If
      Next
      .ParamCount = ParamCount
      .ChipCount = DataCount
   End With
End Function

'======== ����ΪMPW��ʽ�ú��� ===============
' ��ȡ�ྦྷԲ��ʽ�и���Բ���ݵĿ�ʼ��
Private Function GetWaferStartRows(WaferDataSheet As Worksheet)
   Dim Ret: ReDim Ret(1 To 1)
   Dim x: x = WaferDataSheet.UsedRange.Value
   Dim FindCount As Integer: FindCount = 1
   Do
      Dim StartRow As Long: StartRow = FindContentRow(x, "WAFER:", FindCount)
      If StartRow > 0 Then
         If Val(x(StartRow, 3)) > 0 Then
            Dim WaferIndex As Integer: WaferIndex = WaferIndex + 1
            ReDim Preserve Ret(1 To WaferIndex)
            Ret(FindCount) = StartRow  ' ��¼��Բ���ݿ�ʼ��
         End If
         FindCount = FindCount + 1
      End If
   Loop While StartRow > 0
   GetWaferStartRows = Ret
End Function

' �����������в���ָ���������ڵ���
Private Function FindContentRow(x, toFind, Optional FindCount As Integer = 1) As Long
   Dim i As Long
   For i = 1 To UBound(x)
      If x(i, 1) = toFind Then
         Dim myCount As Integer: myCount = myCount + 1
         If myCount = FindCount Then FindContentRow = i: Exit Function
      End If
   Next
End Function

' ��CW��ʽ�ྦྷԲ�ļ�����ȡ��Ϣ��TestInfo����
Public Function SplitInfo_CWMW(TestInfo As CPLot, WaferDataSheet As Worksheet)
   
   WaferDataSheet.UsedRange.Replace What:="Untested", Replacement:="", LookAt:=xlWhole  ' �滻"Untested"Ϊ��
   
   Dim WaferStartRows: WaferStartRows = GetWaferStartRows(WaferDataSheet)  ' ��ȡ���о�Բ���ݵĿ�ʼ��
   
   Dim WaferCount As Integer: WaferCount = SizeOf(WaferStartRows)
   If WaferCount = 0 Then Exit Function
   
   With TestInfo
      .WaferCount = WaferCount
      ReDim .Wafers(1 To WaferCount)
      Dim WaferIndex As Integer: For WaferIndex = 1 To WaferCount
         If .ParamCount = 0 Then AddParamInfo TestInfo, WaferDataSheet, MWFlag:=True  ' ��Ӳ�����Ϣ��ָ��Ϊ�ྦྷԲ��ʽ
         AddWaferInfo .Wafers(WaferIndex), WaferDataSheet, .ParamCount, WaferStartRows(WaferIndex)  ' ��Ӿ�Բ��Ϣ
      Next
   End With
End Function
