Attribute VB_Name = "MEX格式数据采集"
Option Explicit

' 定义MEX格式数据文件的列和行常量
Const PARAM_START_COL As Integer = 8  ' 参数起始列
Const STD_ITEM_ROW As Long = 11      ' 标准项目行
Const USER_ITEM_ROW As Long = 12     ' 用户项目行
Const UPPER_ROW As Long = 13         ' 上限行
Const LOWER_ROW As Long = 14         ' 下限行
Const COND_START_ROW As Long = 15    ' 测试条件开始行
Const COND_END_ROW As Long = 20      ' 测试条件结束行

Const DATA_START_ROW As Integer = 27 ' 数据开始行
Const SEQ_COL As Integer = 1         ' 序号列
Const WAFER_COL As Integer = 2       ' 晶圆ID列
Const X_COL As Integer = 3           ' X坐标列
Const Y_COL As Integer = 4           ' Y坐标列
Const BIN_COL As Integer = 5         ' Bin列

Dim ParamPos() As Integer '数组序为表的列序,内容为参数的序

' 从MEX格式文件中提取信息到TestInfo对象
Function SplitInfo_MEX(TestInfo As CPLot, WaferDataSheet As Worksheet, WaferIndex)
   WaferDataSheet.UsedRange.Replace What:=" ----", Replacement:="", LookAt:=xlWhole  ' 替换" ----"为空
   With TestInfo
      If .ParamCount = 0 Then AddParamInfo TestInfo, WaferDataSheet, ParamPos  ' 如果是第一片，添加参数信息
      AddWaferInfo .Wafers(WaferIndex), WaferDataSheet, .ParamCount  ' 添加晶圆信息
   End With
End Function

' 添加参数信息
Private Function AddParamInfo(ByRef LotInfo As CPLot, WaferDataSheet As Worksheet, ByRef ParamPos() As Integer)
   Dim WaferData: WaferData = WaferDataSheet.UsedRange.Value
   Dim myParams() As TestItem
   Dim ParamIndex As Integer
   Dim myPos() As Integer: ReDim myPos(1 To UBound(WaferData, 2))
   Dim ColIndex As Integer: For ColIndex = PARAM_START_COL To UBound(WaferData, 2)
      If WaferData(USER_ITEM_ROW, ColIndex) <> "Dischage Time" Then  ' 跳过"Dischage Time"
         ParamIndex = ParamIndex + 1
         myPos(ColIndex) = ParamIndex
         ReDim Preserve myParams(1 To ParamIndex)
         With myParams(ParamIndex)
            .DisplayName = WaferData(USER_ITEM_ROW, ColIndex)  ' 设置显示名称
            .Group = WaferData(USER_ITEM_ROW, ColIndex)        ' 设置组名
            Dim TestNameDic As Object
            .Id = Change2UniqueName(.Group, TestNameDic)       ' 转换为唯一名称
            .Unit = SplitUnit(WaferData(STD_ITEM_ROW, ColIndex))  ' 提取单位
            .SL = ChangeWithUnit(WaferData(LOWER_ROW, ColIndex), .Unit)  ' 设置下限
            .SU = ChangeWithUnit(WaferData(UPPER_ROW, ColIndex), .Unit)  ' 设置上限
            ReDim .TestCond(1 To COND_END_ROW - COND_START_ROW + 1)
            Dim i: For i = 1 To COND_END_ROW - COND_START_ROW + 1
               .TestCond(i) = WaferData(COND_START_ROW + i - 1, ColIndex)  ' 设置测试条件
            Next
         End With
      End If
   Next
   
   ParamPos = myPos
   With LotInfo
      .ParamCount = ParamIndex
      .Params = myParams
      .Product = WaferData(5, 3)  ' 设置产品名，从单元格(5,3)获取
   End With
End Function

' 从标准项目中提取单位信息，单位通常包含在方括号中
Private Function SplitUnit(StdItem) As String
   SplitUnit = SplitContentInPairChar(StdItem, "[]")  ' 提取[]中的内容作为单位
End Function

' 添加晶圆信息
Private Function AddWaferInfo(WaferInfo As CPWafer, _
                              WaferDataSheet As Worksheet, _
                              ParamCount As Integer)
   Dim DataCount As Long: DataCount = WaferDataSheet.UsedRange.Rows.Count - DATA_START_ROW + 1  ' 计算数据点数量
   With WaferInfo
      .WaferId = WaferDataSheet.Cells(DATA_START_ROW, WAFER_COL).Value  ' 设置晶圆ID
      .Seq = GetList(WaferDataSheet, SEQ_COL, DATA_START_ROW, DataCount)  ' 获取序号列表
      .Bin = GetList(WaferDataSheet, BIN_COL, DATA_START_ROW, DataCount)  ' 获取Bin值列表
      .x = GetList(WaferDataSheet, X_COL, DATA_START_ROW, DataCount)      ' 获取X坐标列表
      .Y = GetList(WaferDataSheet, Y_COL, DATA_START_ROW, DataCount)      ' 获取Y坐标列表
      .Width = WorksheetFunction.Max(.x) - WorksheetFunction.Min(.x) + 2  ' 计算晶圆宽度
      ReDim .ChipDatas(1 To ParamCount)
      Dim i As Integer: For i = LBound(ParamPos) To UBound(ParamPos)
         If ParamPos(i) > 0 Then
            .ChipDatas(ParamPos(i)) = GetList(WaferDataSheet, i, DATA_START_ROW, DataCount)  ' 获取芯片数据
         End If
      Next
      .ParamCount = ParamCount
      .ChipCount = DataCount
   End With
End Function


