Attribute VB_Name = "DCP格式数据采集"
Option Explicit

' 定义DCP格式数据文件的列和行常量
Const PARAM_START_COL As Integer = 5  ' 参数起始列
Const STD_ITEM_ROW As Long = 7       ' 标准项目行
Const USER_ITEM_ROW As Long = 7      ' 用户项目行
Const UPPER_ROW As Long = 8          ' 上限行
Const LOWER_ROW As Long = 9          ' 下限行
Const COND_START_ROW As Long = 10    ' 测试条件开始行
Const COND_END_ROW As Long = 15      ' 测试条件结束行

Const DATA_START_ROW As Integer = 16 ' 数据开始行
Const SEQ_COL As Integer = 1         ' 序号列
Const X_COL As Integer = 2           ' X坐标列
Const Y_COL As Integer = 3           ' Y坐标列
Const BIN_COL As Integer = 4         ' Bin列

Dim ParamPos() As Integer '数组序为表的列序,内容为参数的序

' 检查并确保第6行为空行，如果不是则插入一个空行
Public Sub CheckSixthRow(WaferDataSheet As Worksheet)
   With WaferDataSheet
      If .Cells(6, 1) <> "" Then
         .Rows(6).Insert  ' 在第6行插入一个空行
      End If
   End With
End Sub

' 从DCP格式文件中提取信息到TestInfo对象
Function SplitInfo_DCP(TestInfo As CPLot, WaferDataSheet As Worksheet, WaferIndex)
   CheckSixthRow WaferDataSheet  ' 确保第6行为空行
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
            .Unit = SplitUnit(WaferData(LOWER_ROW, ColIndex))  ' 提取单位
            .SL = ChangeVal(WaferData(LOWER_ROW, ColIndex))    ' 设置下限
            .SU = ChangeVal(WaferData(UPPER_ROW, ColIndex))    ' 设置上限
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
      .Product = Replace(WaferData(1, 2), ".dcp", "")  ' 设置产品名，去除.dcp后缀
   End With
End Function

' 根据单位转换值
Private Function ChangeVal(spec)
   Dim Ret
   With RegEx
      Ret = Val(spec) * CalRate(.LastSubMatchValue("\d+(\.\d+)?([munpfk]?)(?:V|A|OHM)", spec))  ' 使用正则表达式提取单位并计算换算率
   End With
   ChangeVal = Ret
End Function

' 计算单位换算率
Private Function CalRate(RateStr)
   Dim Ret
   Select Case LCase(RateStr)
   Case "m"
      Ret = 0.001          ' 毫 (milli)
   Case "u"
      Ret = 0.000001       ' 微 (micro)
   Case "n"
      Ret = 0.000000001    ' 纳 (nano)
   Case "p"
      Ret = 0.000000000001 ' 皮 (pico)
   Case "f"
      Ret = 0.000000000000001 ' 飞 (femto)
   Case "k"
      Ret = 1000           ' 千 (kilo)
   Case Else
      Ret = 1              ' 无单位前缀
   End Select
   CalRate = Ret
End Function

' 从规格字符串中提取单位
Private Function SplitUnit(spec) As String
   Dim Ret As String
   With RegEx
      Ret = .LastSubMatchValue("\d+(\.\d+)?[munpfk]?(V|A|OHM)", spec)  ' 使用正则表达式提取单位
   End With
   SplitUnit = Ret
End Function

' 添加晶圆信息
Private Function AddWaferInfo(WaferInfo As CPWafer, _
                              WaferDataSheet As Worksheet, _
                              ParamCount As Integer)
   Dim DataCount As Long: DataCount = WaferDataSheet.UsedRange.Rows.Count - DATA_START_ROW + 1  ' 计算数据点数量
   With WaferInfo
      .WaferId = WaferDataSheet.Cells(3, 2).Value  ' 设置晶圆ID
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




