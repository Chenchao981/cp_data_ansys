Attribute VB_Name = "CW格式数据采集"
Option Explicit

' 定义CW格式数据文件的列和行常量
Const PARAM_START_COL As Integer = 11      ' 参数数据起始列
Const STD_ITEM_ROW As Long = 14           ' 标准项目行
Const USER_ITEM_ROW As Long = 15          ' 用户项目行
Const LIMIT_ROW As Long = 16              ' 限制值行
Const COND_START_ROW As Long = 17         ' 测试条件开始行
Const COND_END_ROW As Long = 18           ' 测试条件结束行

Const UNIT_RATE_ROW As Integer = 20       ' 单位换算行
Const DATA_START_ROW As Integer = 30      ' 数据开始行
Const SEQ_COL As Integer = 1              ' 序号列
Const BIN_COL As Integer = 2              ' Bin值列
Const X_COL As Integer = 3                ' X坐标列
Const Y_COL As Integer = 5                ' Y坐标列

Dim ParamPos() As Integer '数组序为表的列序,内容为参数的序

' 从CW格式单晶圆文件中提取信息到TestInfo对象
Public Function SplitInfo_CWSW(TestInfo As CPLot, WaferDataSheet As Worksheet, WaferIndex)
   WaferDataSheet.UsedRange.Replace What:="Untested", Replacement:="", LookAt:=xlWhole  ' 替换"Untested"为空
   With TestInfo
      If .ParamCount = 0 Then AddParamInfo TestInfo, WaferDataSheet  ' 如果是第一片，添加参数信息
      AddWaferInfo .Wafers(WaferIndex), WaferDataSheet, .ParamCount  ' 添加晶圆信息
   End With
End Function

' 获取下一个项目名称
Private Function GetNextItemName(WaferData, CurItemCol) As String
   Dim Ret As String
   Dim NextItemCol As Integer: NextItemCol = CurItemCol + 2
   If NextItemCol <= UBound(WaferData, 2) Then Ret = WaferData(USER_ITEM_ROW, NextItemCol)
   GetNextItemName = Ret
End Function

' 判断下一个项目是否为"same"
Private Function NextItemIsSame(WaferData, CurItemCol) As Boolean
   Dim Ret As Boolean
   Dim NextItemName As String
   NextItemName = LCase(GetNextItemName(WaferData, CurItemCol))
   Ret = ("same" = NextItemName)
   NextItemIsSame = Ret
End Function

' 根据参数名猜测参数质量控制方式（上限或下限）
Private Function GuessParamQC(Param) As String
   Dim Ret As String
   Ret = IIf(UCase(Left(Param, 1)) = "B", "ExceptHi", "ExceptLow")  ' 如果参数名以B开头，猜测为上限控制，否则为下限控制
   GuessParamQC = Ret
End Function

' 设置参数的限制值
Private Function SetupLimit(WaferData, ColIndex, Param As TestItem)
   Dim Limit: Limit = WaferData(LIMIT_ROW, ColIndex)
   With Param
      .Unit = Trim(Right(Limit, 2))  ' 获取单位
      If NextItemIsSame(WaferData, ColIndex) Then
         .SL = Val(Limit)  ' 当前列为下限
         .SU = Val(WaferData(LIMIT_ROW, ColIndex + 2))  ' 后两列为上限
      Else
         If GuessParamQC(.Group) = "ExceptHi" Then
            .SL = Val(Limit)  ' 猜测为上限控制，设置下限
         Else
            .SU = Val(Limit)  ' 猜测为下限控制，设置上限
         End If
      End If
   End With
End Function

' 添加参数信息
Private Function AddParamInfo(ByRef LotInfo As CPLot, WaferDataSheet As Worksheet, Optional MWFlag As Boolean = False)
   Dim WaferData: WaferData = WaferDataSheet.UsedRange.Value
   Dim myParams() As TestItem
   Dim ParamIndex As Integer
   Dim myPos() As Integer: ReDim myPos(1 To UBound(WaferData, 2))
   Dim ColIndex As Integer: For ColIndex = PARAM_START_COL To UBound(WaferData, 2)
      Dim toCheckName As String: toCheckName = WaferData(USER_ITEM_ROW, ColIndex)
      If toCheckName <> "SAME" And toCheckName <> "" Then  ' 跳过"SAME"和空名称
         ParamIndex = ParamIndex + 1
         myPos(ColIndex) = ParamIndex
         ReDim Preserve myParams(1 To ParamIndex)
         With myParams(ParamIndex)
            .DisplayName = WaferData(USER_ITEM_ROW, ColIndex)  ' 设置显示名称
            .Group = WaferData(USER_ITEM_ROW, ColIndex)        ' 设置组名
            Dim TestNameDic As Object
            .Id = Change2UniqueName(.Group, TestNameDic)       ' 转换为唯一名称
            SetupLimit WaferData, ColIndex, myParams(ParamIndex)  ' 设置限制值
            ReDim .TestCond(1 To COND_END_ROW - COND_START_ROW + 1)
            Dim i: For i = 1 To COND_END_ROW - COND_START_ROW + 1
               .TestCond(i) = WaferData(COND_START_ROW + i - 1, ColIndex)  ' 设置测试条件
            Next
            WaferDataSheet.Cells(UNIT_RATE_ROW, ColIndex) = ChangeWithUnit(1, .Unit)  ' 设置单位换算
         End With
      End If
   Next
   
   ParamPos = myPos
   With LotInfo
      .ParamCount = ParamIndex
      .Params = myParams
      If MWFlag Then
         .Product = WaferDataSheet.Name  ' 多晶圆时产品名为工作表名
      Else
         .Product = Split(WaferDataSheet.Name, "-")(0)  ' 单晶圆时产品名为工作表名的第一部分
      End If
   End With
End Function

' 从文件名中提取晶圆编号
Private Function SplitWaferNoFromFileName(tmpFileName)
   Dim Pos As Long
   Pos = InStrRev(tmpFileName, "-")
   If Pos > 0 Then
      SplitWaferNoFromFileName = Mid(tmpFileName, Pos + 1, Len(tmpFileName) - Pos - 4)
   End If
End Function

' 从文件名中提取批次信息
Private Function SplitLot(tmpFileName)
   Dim s: s = tmpFileName
   Dim Pos As Long: Pos = InStrRev(s, "-")
   If Pos > 0 Then SplitLot = Left(s, Pos - 1)
End Function

' 添加晶圆信息
Private Function AddWaferInfo(WaferInfo As CPWafer, _
                              WaferDataSheet As Worksheet, _
                              ParamCount As Integer, _
                              Optional WaferStartRow)
   Dim myStartRow As Long
   If IsMissing(WaferStartRow) Then
      myStartRow = DATA_START_ROW  ' 使用默认数据开始行
   Else
      myStartRow = WaferStartRow   ' 使用指定的数据开始行
   End If
   
   Dim DataCount As Long: DataCount = WaferDataSheet.Cells(myStartRow, 3)  ' 获取芯片数量
   Dim DataStartRow As Long: DataStartRow = myStartRow + 3  ' 实际数据开始行
   With WaferInfo
      If IsMissing(WaferStartRow) Then
         .WaferId = Right(WaferDataSheet.Name, 2)  ' 单晶圆时，从工作表名称中提取晶圆ID
      Else
         .WaferId = WaferDataSheet.Cells(myStartRow, 2)  ' 多晶圆时，从单元格获取晶圆ID
      End If
      .Seq = GetList(WaferDataSheet, SEQ_COL, DataStartRow, DataCount)  ' 获取序号列表
      .Bin = GetList(WaferDataSheet, BIN_COL, DataStartRow, DataCount)  ' 获取Bin值列表
      .x = GetList(WaferDataSheet, X_COL, DataStartRow, DataCount)      ' 获取X坐标列表
      .Y = GetList(WaferDataSheet, Y_COL, DataStartRow, DataCount)      ' 获取Y坐标列表
      .Width = WorksheetFunction.Max(.x) - WorksheetFunction.Min(.x) + 2  ' 计算晶圆宽度
      ReDim .ChipDatas(1 To ParamCount)
      Dim i As Integer: For i = LBound(ParamPos) To UBound(ParamPos)
         If ParamPos(i) > 0 Then
            Dim UnitRateCell As Range
            Set UnitRateCell = WaferDataSheet.Cells(UNIT_RATE_ROW, i)
            UnitRateCell = ChangeWithUnit(1, Right(WaferDataSheet.Cells(LIMIT_ROW, i), 2))  ' 设置单位换算
            Dim ChipDataRng As Range
            Set ChipDataRng = GetList(WaferDataSheet, i, DataStartRow, DataCount)
            ChangeRangeUnit UnitRateCell, ChipDataRng  ' 应用单位换算
            .ChipDatas(ParamPos(i)) = ChipDataRng.Value  ' 存储芯片数据
         End If
      Next
      .ParamCount = ParamCount
      .ChipCount = DataCount
   End With
End Function

'======== 以下为MPW格式用函数 ===============
' 获取多晶圆格式中各晶圆数据的开始行
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
            Ret(FindCount) = StartRow  ' 记录晶圆数据开始行
         End If
         FindCount = FindCount + 1
      End If
   Loop While StartRow > 0
   GetWaferStartRows = Ret
End Function

' 在数据数组中查找指定内容所在的行
Private Function FindContentRow(x, toFind, Optional FindCount As Integer = 1) As Long
   Dim i As Long
   For i = 1 To UBound(x)
      If x(i, 1) = toFind Then
         Dim myCount As Integer: myCount = myCount + 1
         If myCount = FindCount Then FindContentRow = i: Exit Function
      End If
   Next
End Function

' 从CW格式多晶圆文件中提取信息到TestInfo对象
Public Function SplitInfo_CWMW(TestInfo As CPLot, WaferDataSheet As Worksheet)
   
   WaferDataSheet.UsedRange.Replace What:="Untested", Replacement:="", LookAt:=xlWhole  ' 替换"Untested"为空
   
   Dim WaferStartRows: WaferStartRows = GetWaferStartRows(WaferDataSheet)  ' 获取所有晶圆数据的开始行
   
   Dim WaferCount As Integer: WaferCount = SizeOf(WaferStartRows)
   If WaferCount = 0 Then Exit Function
   
   With TestInfo
      .WaferCount = WaferCount
      ReDim .Wafers(1 To WaferCount)
      Dim WaferIndex As Integer: For WaferIndex = 1 To WaferCount
         If .ParamCount = 0 Then AddParamInfo TestInfo, WaferDataSheet, MWFlag:=True  ' 添加参数信息，指定为多晶圆格式
         AddWaferInfo .Wafers(WaferIndex), WaferDataSheet, .ParamCount, WaferStartRows(WaferIndex)  ' 添加晶圆信息
      Next
   End With
End Function
