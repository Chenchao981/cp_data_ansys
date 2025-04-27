Attribute VB_Name = "散点图制作"
Option Explicit

' 定义用户自定义坐标轴设置的结构
Type UserCoordinateSetup
   TestItem As String        ' 坐标轴对应的测试项目名称 (来自 Params().Id)
   SetupMethod As String     ' 坐标轴刻度设置方法 ("自动" 或 "手工指定")
   MinimumScale As Variant   ' 手工指定的最小刻度
   MaximumScale As Variant   ' 手工指定的最大刻度
   AxisTitle As String       ' 自定义的坐标轴标题 (如果为空，则使用 TestItem)
End Type

' 定义单个散点图的完整设置信息
Type ScatterPlotChartSetup
   Title As String             ' 图表标题 (用户自定义部分)
   XAxis As UserCoordinateSetup ' X 轴设置
   YAxis As UserCoordinateSetup ' Y 轴设置
   WaferCount As Integer       ' 该图表设置对应的 Wafer 数量 (通常等于 Lot 中的 Wafer 总数)
   WaferCode() As String       ' Wafer 编号列表 (来自 TestInfo.Wafers(i).WaferId)
   ValueRng() As Range         ' Y 轴数据源 Range 对象数组 (每个元素对应一个 Wafer 的 Y 轴数据)
   XValueRng() As Range        ' X 轴数据源 Range 对象数组 (每个元素对应一个 Wafer 的 X 轴数据)
End Type

' 定义散点图样本信息，包含模板图表对象和多个图表设置
Type ScatterPlotSample
   SampleChartObject As ChartObject    ' 作为模板的图表对象 (来自 XY_SETUP_SHEET)
   ChartCount As Integer             ' 需要生成的图表总数 (根据 XY_SETUP_SHEET 的设置列数决定)
   ChartSetup() As ScatterPlotChartSetup ' 存储每个图表设置的数组
End Type

' 主函数：根据设置生成所有散点图
Public Function PlotScatterChart(ResultBook As Workbook, _
                                 SampleSheet As Worksheet, _
                                 myTestinfo As CPLot)
   With ResultBook
      Dim d As Worksheet: Set d = .Worksheets("Data") ' 数据源工作表
      Dim s As Worksheet: Set s = .Worksheets("Scatter") ' 目标图表工作表
   End With
   Dim mySample As ScatterPlotSample
   ' 1. 读取模板和设置，并关联数据源
   mySample = CreateScatterPlotSample(d, SampleSheet, myTestinfo)
   ' 2. 根据读取到的设置和数据，逐个生成图表
   PlotBySample mySample, s
End Function

' 根据样本设置 (mySample) 循环生成所有图表到目标工作表 (PlotSheet)
Private Function PlotBySample(mySample As ScatterPlotSample, PlotSheet As Worksheet)
   With mySample
      ' 遍历每个图表设置 (ChartSetup)
      Dim ChartIndex: For ChartIndex = 1 To .ChartCount
         ' 遍历该设置对应的每个 Wafer
         Dim Wafer: For Wafer = 1 To .ChartSetup(ChartIndex).WaferCount
            ' 为当前 ChartIndex 和 WaferIndex 创建一个新的图表
            CreateNewChart mySample, PlotSheet, ChartIndex, Wafer
         Next
      Next
   End With
End Function

' 创建单个新的散点图
Public Function CreateNewChart(mySample As ScatterPlotSample, _
                               PlotSheet As Worksheet, _
                               ChartIndex, WaferIndex)
   
   Dim Title As String
   Dim XAxis As UserCoordinateSetup
   Dim YAxis As UserCoordinateSetup
   Dim Xvalues As Range
   Dim Yvalues As Range
   
   ' 从 mySample 中提取当前图表所需的信息
   With mySample
      With .ChartSetup(ChartIndex)
         ' 构建图表标题: WaferID# + (用户自定义标题 或 X-Y项目名) + " Chart"
         Title = .WaferCode(WaferIndex) & "# "
         Title = Title & FirstVaildContent(.Title, .XAxis.TestItem & "-" & .YAxis.TestItem)
         Title = Title & " Chart"
         ' 获取 X, Y 轴设置和数据源
         XAxis = .XAxis
         YAxis = .YAxis
         Set Xvalues = .XValueRng(WaferIndex)
         Set Yvalues = .ValueRng(WaferIndex)
      End With
      ' 复制模板图表
      .SampleChartObject.Copy
   End With
   
   ' 在目标工作表粘贴并设置新图表
   With PlotSheet
      .Paste
      With .ChartObjects(.ChartObjects.Count) ' 操作刚刚粘贴的图表对象
         ' 设置图表位置 (按 ChartIndex 水平排列，按 WaferIndex 垂直排列)
         .Left = 10 + (ChartIndex - 1) * (20 + .Width)
         .Top = 10 + (WaferIndex - 1) * (.Height + 20)
         With .Chart
            ' 更新 X, Y 坐标轴的刻度和标题
            UpdateAxis .Axes(xlCategory), XAxis ' X 轴
            UpdateAxis .Axes(xlValue), YAxis    ' Y 轴
            .HasTitle = True
            .ChartTitle.Text = Title ' 设置图表标题
            ' 更新数据系列的数据源
            If .SeriesCollection.Count > 0 Then ' 确保模板图表有数据系列
               With .SeriesCollection(1)
                  .Name = "x-y" ' 系列名称
                  .Xvalues = Xvalues ' X 轴数据
                  .Values = Yvalues  ' Y 轴数据
               End With
            Else
               ' 如果模板没有系列，可以考虑添加一个新的
               ' Dim sc As Series: Set sc = .SeriesCollection.NewSeries
               ' sc.ChartType = xlXYScatter
               ' sc.Name = "x-y"
               ' sc.Xvalues = Xvalues
               ' sc.Values = Yvalues
            End If
         End With
      End With
   End With
End Function

' 更新坐标轴的设置 (刻度、标题)
Private Function UpdateAxis(myAxis As Axis, _
                            myAxisSetup As UserCoordinateSetup)
   With myAxisSetup
      ' 如果设置为手工指定刻度
      If .SetupMethod = "手工指定" Then
         If Not IsEmpty(.MinimumScale) And IsNumeric(.MinimumScale) Then
            myAxis.MinimumScale = .MinimumScale
            myAxis.MinimumScaleIsAuto = False
         Else
            myAxis.MinimumScaleIsAuto = True
         End If
         If Not IsEmpty(.MaximumScale) And IsNumeric(.MaximumScale) Then
            myAxis.MaximumScale = .MaximumScale
            myAxis.MaximumScaleIsAuto = False
         Else
            myAxis.MaximumScaleIsAuto = True
         End If
      Else ' 如果是自动刻度
            myAxis.MinimumScaleIsAuto = True
            myAxis.MaximumScaleIsAuto = True
      End If
      ' 设置坐标轴标题 (优先使用自定义标题，否则使用测试项目名称)
      myAxis.HasTitle = True
      myAxis.AxisTitle.Text = FirstVaildContent(.AxisTitle, .TestItem)
   End With
End Function

' 创建 ScatterPlotSample 结构，包含模板图表、所有图表设置，并关联数据源
Private Function CreateScatterPlotSample(DataSheet As Worksheet, _
                                         ChartSampleSheet As Worksheet, _
                                         myTestinfo As CPLot) As ScatterPlotSample
   Dim Ret As ScatterPlotSample
   ' 1. 获取模板图表对象 (假设在 ChartSampleSheet 的第一个 ChartObject)
   Set Ret.SampleChartObject = ChartSampleSheet.ChartObjects(1)
   ' 2. 从 ChartSampleSheet 读取用户定义的图表设置 (X/Y轴项目、刻度、标题等)
   AddSetupInfo ChartSampleSheet, Ret
   ' 3. 根据设置，从 DataSheet 关联每个图表设置所需的 X/Y 数据源 Range
   AddWaferData Ret, DataSheet, myTestinfo
   CreateScatterPlotSample = Ret
End Function

' 从散点图设置工作表 (ChartSampleSheet) 读取用户定义的图表设置信息
Private Function AddSetupInfo(ChartSampleSheet As Worksheet, Ret As ScatterPlotSample)
   Dim ContentArray
   On Error Resume Next
   ContentArray = ChartSampleSheet.Range("a1").CurrentRegion.Value
   If Err.Number <> 0 Or Not IsArray(ContentArray) Then Exit Function ' 读取失败或区域为空则退出
   On Error GoTo 0
   
   If UBound(ContentArray, 2) < 2 Then Exit Function ' 至少需要两列 (标题行 + 一列设置)
   
   Dim ColIndex As Integer: For ColIndex = 2 To UBound(ContentArray, 2)
      ' 检查 X 轴和 Y 轴的测试项目名称是否都已填写 (第5行和第11行)
      If ContentArray(5, ColIndex) <> "" And ContentArray(11, ColIndex) <> "" Then
         With Ret
            .ChartCount = .ChartCount + 1
            ReDim Preserve .ChartSetup(1 To .ChartCount)
            With .ChartSetup(.ChartCount)
               .Title = ContentArray(3, ColIndex) ' 图表标题 (用户定义)
               .XAxis = CreateNewUserCoordinateSetup(ContentArray, ColIndex, 4) ' 读取 X 轴设置
               .YAxis = CreateNewUserCoordinateSetup(ContentArray, ColIndex, 10) ' 读取 Y 轴设置
            End With
         End With
      End If
   Next
End Function

' 根据从设置表读取的数组和列索引，创建单个 UserCoordinateSetup 结构
Private Function CreateNewUserCoordinateSetup(ContentArray, _
                                              ColIndex As Integer, _
                                              StartRow As Long) As UserCoordinateSetup
   Dim Ret As UserCoordinateSetup
   With Ret
      .TestItem = ContentArray(StartRow + 1, ColIndex)    ' 测试项目名称
      .SetupMethod = ContentArray(StartRow + 2, ColIndex) ' 刻度设置方法
      If .SetupMethod = "手工指定" Then
         .MinimumScale = ContentArray(StartRow + 3, ColIndex) ' 最小刻度
         .MaximumScale = ContentArray(StartRow + 4, ColIndex) ' 最大刻度
      End If
      .AxisTitle = ContentArray(StartRow + 5, ColIndex)    ' 坐标轴标题
   End With
   CreateNewUserCoordinateSetup = Ret
End Function

' 为 ScatterPlotSample 中的每个图表设置关联实际的数据源 Range
Private Function AddWaferData(mySample As ScatterPlotSample, _
                              DataSheet As Worksheet, _
                              myTestinfo As CPLot)
   ' 1. 创建 Wafer 信息数组 (包含 WaferCode 和每个 Wafer 数据区域的起始行信息)
   Dim WaferRowInfo: WaferRowInfo = CreateWaferInfo(myTestinfo, DataSheet)
   ' 2. 创建测试项目名称到 DataSheet 列索引的映射字典
   Dim TestItemColDic As Object: Set TestItemColDic = CreateTestItemColDic(myTestinfo)
   
   With mySample
      Dim ChartIndex As Integer: For ChartIndex = 1 To .ChartCount
         With .ChartSetup(ChartIndex)
            .WaferCount = myTestinfo.WaferCount
            .WaferCode = WaferRowInfo(1) ' 关联 Wafer 编号列表
            ' 根据 X/Y 轴设置的 TestItem 名称，查找对应的列索引，并获取每个 Wafer 的数据 Range
            .XValueRng = GetPlotDataRng(.XAxis.TestItem, WaferRowInfo(2), TestItemColDic)
            .ValueRng = GetPlotDataRng(.YAxis.TestItem, WaferRowInfo(2), TestItemColDic)
         End With
      Next
   End With
End Function

' 创建一个包含 WaferCode 列表和每个 Wafer 在 DataSheet 中数据范围的数组
' 返回值: 一个二维数组 Ret(1 to 2)
' Ret(1): 包含所有 WaferId 的一维数组
' Ret(2): 包含每个 Wafer 数据区域 (A列) 的 Range 对象的一维数组
Private Function CreateWaferInfo(myTestinfo As CPLot, DataSheet As Worksheet)
   Dim Ret: ReDim Ret(1 To 2)
   With myTestinfo
      If .WaferCount = 0 Then Exit Function
      Dim WaferRng() As Range: ReDim WaferRng(1 To .WaferCount)
      Dim WaferCode() As String: ReDim WaferCode(1 To .WaferCount)
      Dim StartRow As Long: StartRow = 2 ' 数据从第 2 行开始
      Dim i: For i = 1 To .WaferCount
         With .Wafers(i)
           Dim DataRows As Long: DataRows = .ChipCount
           WaferCode(i) = .WaferId
           Set WaferRng(i) = DataSheet.Cells(StartRow, 1).Resize(DataRows) ' 获取 A 列的数据范围
           StartRow = StartRow + DataRows ' 更新下一个 Wafer 的起始行
         End With
      Next
   End With
   Ret(1) = WaferCode
   Ret(2) = WaferRng
   CreateWaferInfo = Ret
End Function

' 创建一个从测试项目名称 (TestItem.Id) 到其在 DataSheet 中对应列号的映射字典
Private Function CreateTestItemColDic(myTestinfo As CPLot) As Object
   Dim Ret As Object: Set Ret = CreateObject("scripting.dictionary")
   Ret.CompareMode = vbTextCompare ' 设置字典键值比较为不区分大小写
   Dim DataStartCol As Long: DataStartCol = 6 ' 数据列从第 6 列 (F列) 开始
   With myTestinfo
      Dim i: For i = 1 To .ParamCount
         With .Params(i)
            Dim TestItemName As String: TestItemName = .Id
            ' 处理可能的重名情况 (虽然 CPLot 结构中 Id 应该是唯一的)
            Dim k As Integer: k = 1
            Do While Ret.exists(TestItemName)
               k = k + 1
               TestItemName = .Id & k
            Loop
            Ret.Add TestItemName, i + DataStartCol - 1 ' 存储 ItemName -> 列号 的映射
         End With
      Next
   End With
   Set CreateTestItemColDic = Ret
End Function

' 根据测试项目名称 (TestItem) 从映射字典中获取列号，并返回每个 Wafer 对应列的数据 Range 数组
Private Function GetPlotDataRng(TestItem As String, WaferRngs, TestItemColDic As Object)
   Dim DataCol As Variant
   DataCol = TestItemColDic(TestItem) ' 从字典获取列号
   If IsEmpty(DataCol) Then
       gShow.ErrStop "散点图设置错误", OCAP:="测试项目名称 '" & TestItem & "' 在数据表中未找到对应的列。"
       End ' 终止宏
   End If
   GetPlotDataRng = WaferRngOffset(WaferRngs, CInt(DataCol))
End Function

' 根据 Wafer 的 A 列 Range 数组 (WaferRngList) 和目标列号 (TestItemCol)，计算每个 Wafer 对应目标列的数据 Range 数组
Private Function WaferRngOffset(WaferRngList, TestItemCol As Integer) As Range()
   Dim Ret() As Range
   If Not IsArray(WaferRngList) Then Exit Function
   ReDim Ret(LBound(WaferRngList) To UBound(WaferRngList))
   Dim i: For i = LBound(WaferRngList) To UBound(WaferRngList)
      Set Ret(i) = WaferRngList(i).Offset(0, TestItemCol - 1) ' A 列是第 1 列，所以偏移量是 Col - 1
   Next
   WaferRngOffset = Ret
End Function

' 从可变参数数组中返回第一个非空字符串
Public Function FirstVaildContent(ParamArray argv()) As String
   Dim Ret As String
   Dim s: For Each s In argv
      If Not IsEmpty(s) And Len(Trim(CStr(s))) > 0 Then
         Ret = Trim(CStr(s))
         Exit For
      End If
   Next
   FirstVaildContent = Ret
End Function

' 检查散点图设置 (XY_SETUP_SHEET) 是否有效
Public Function SetupCheck_SCATTER_PLOT(TestInfo As CPLot) As Boolean
   Dim SetupOk As Boolean: SetupOk = True ' 默认设置为 True
   Dim TestItemColDic As Object: Set TestItemColDic = CreateTestItemColDic(TestInfo)
   Dim ContentArray
   
   On Error Resume Next
   ContentArray = XY_SETUP_SHEET.Range("a1").CurrentRegion.Value
   If Err.Number <> 0 Or Not IsArray(ContentArray) Then
       gShow.ErrAlarm "无法读取散点图设置表 (XY_SETUP_SHEET) 的内容。"
       SetupCheck_SCATTER_PLOT = False
       Exit Function
   End If
   On Error GoTo 0
   
   If UBound(ContentArray, 2) < 2 Then SetupCheck_SCATTER_PLOT = True: Exit Function ' 没有设置列，认为 OK
   
   Dim ColIndex As Integer: For ColIndex = 2 To UBound(ContentArray, 2)
      ' 检查 X 轴 (第5行) 和 Y 轴 (第11行) 的 TestItem 是否都已填写
      Dim XItem: XItem = ContentArray(5, ColIndex)
      Dim YItem: YItem = ContentArray(11, ColIndex)
      If XItem <> "" And YItem <> "" Then
         ' 检查 X 轴和 Y 轴的 TestItem 是否在数据列中存在
         If TestItemColDic.exists(XItem) = False Then
            gShow.ErrAlarm Array("错误的XY散点图设置", _
                                 "图 " & ColIndex - 1, _
                                 "X轴项目 [" & XItem & "] 名称不存在或与数据列不匹配。")
            SetupOk = False
         End If
         If TestItemColDic.exists(YItem) = False Then
            gShow.ErrAlarm Array("错误的XY散点图设置", _
                                 "图 " & ColIndex - 1, _
                                 "Y轴项目 [" & YItem & "] 名称不存在或与数据列不匹配。")
            SetupOk = False
         End If
      End If
   Next
   SetupCheck_SCATTER_PLOT = SetupOk
End Function

