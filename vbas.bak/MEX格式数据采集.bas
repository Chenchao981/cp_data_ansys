Attribute VB_Name = "MEX��ʽ���ݲɼ�"
Option Explicit

' ����MEX��ʽ�����ļ����к��г���
Const PARAM_START_COL As Integer = 8  ' ������ʼ��
Const STD_ITEM_ROW As Long = 11      ' ��׼��Ŀ��
Const USER_ITEM_ROW As Long = 12     ' �û���Ŀ��
Const UPPER_ROW As Long = 13         ' ������
Const LOWER_ROW As Long = 14         ' ������
Const COND_START_ROW As Long = 15    ' ����������ʼ��
Const COND_END_ROW As Long = 20      ' ��������������

Const DATA_START_ROW As Integer = 27 ' ���ݿ�ʼ��
Const SEQ_COL As Integer = 1         ' �����
Const WAFER_COL As Integer = 2       ' ��ԲID��
Const X_COL As Integer = 3           ' X������
Const Y_COL As Integer = 4           ' Y������
Const BIN_COL As Integer = 5         ' Bin��

Dim ParamPos() As Integer '������Ϊ�������,����Ϊ��������

' ��MEX��ʽ�ļ�����ȡ��Ϣ��TestInfo����
Function SplitInfo_MEX(TestInfo As CPLot, WaferDataSheet As Worksheet, WaferIndex)
   WaferDataSheet.UsedRange.Replace What:=" ----", Replacement:="", LookAt:=xlWhole  ' �滻" ----"Ϊ��
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
            .Unit = SplitUnit(WaferData(STD_ITEM_ROW, ColIndex))  ' ��ȡ��λ
            .SL = ChangeWithUnit(WaferData(LOWER_ROW, ColIndex), .Unit)  ' ��������
            .SU = ChangeWithUnit(WaferData(UPPER_ROW, ColIndex), .Unit)  ' ��������
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
      .Product = WaferData(5, 3)  ' ���ò�Ʒ�����ӵ�Ԫ��(5,3)��ȡ
   End With
End Function

' �ӱ�׼��Ŀ����ȡ��λ��Ϣ����λͨ�������ڷ�������
Private Function SplitUnit(StdItem) As String
   SplitUnit = SplitContentInPairChar(StdItem, "[]")  ' ��ȡ[]�е�������Ϊ��λ
End Function

' ��Ӿ�Բ��Ϣ
Private Function AddWaferInfo(WaferInfo As CPWafer, _
                              WaferDataSheet As Worksheet, _
                              ParamCount As Integer)
   Dim DataCount As Long: DataCount = WaferDataSheet.UsedRange.Rows.Count - DATA_START_ROW + 1  ' �������ݵ�����
   With WaferInfo
      .WaferId = WaferDataSheet.Cells(DATA_START_ROW, WAFER_COL).Value  ' ���þ�ԲID
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


