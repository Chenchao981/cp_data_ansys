Attribute VB_Name = "BoxPlotChart"
Option Explicit

' 箱线图参数数据类型
Public Type BoxPlotChartParam
   Q1 As Double        ' 第一四分位数
   Q2 As Double        ' 中位数（第二四分位数）
   Q3 As Double        ' 第三四分位数
   PlotMin As Double   ' 箱线图下限（去除异常值）
   PlotMax As Double   ' 箱线图上限（去除异常值）
End Type

' 复制晶圆参数数据到绘图工作表
Private Function CopyWaferFact(PlotSheet As Worksheet) As Range
   Dim Ret As Range
   With FACTOR_SHEET.Range("a1").CurrentRegion
      If .Rows.Count = 1 Then Exit Function  ' 如果数据只有表头则退出
      Dim x: ReDim x(1 To .Columns.Count, 1 To .Rows.Count)
      Dim i: For i = 1 To .Rows.Count
         Dim j: For j = 1 To .Columns.Count
            x(j, i) = .Cells(i, j)  ' 按列优先复制数据
         Next
      Next
   End With
   Set Ret = PlotSheet.Range("b2").Resize(UBound(x), UBound(x, 2))
   Ret.Value = x  ' 填充数据表
   Set CopyWaferFact = Ret
End Function

' 绘制所有参数的箱线图
Public Function PlotAllParamBoxChart(ResultBook As Workbook, myTestinfo As CPLot, WaferQtyOkFlag As Boolean)
   Dim PlotSheet As Worksheet: Set PlotSheet = ResultBook.Worksheets("BoxPlot")
   Dim myBoxPlotChartParam() As BoxPlotChartParam: myBoxPlotChartParam = CalBoxChart(myTestinfo)  ' 计算箱线图参数
   Dim ChartCount As Integer
   With BOXPLOT_SHEET
      Dim WaferRange As Range: Set WaferRange = .Cells(1, 1).Resize(myTestinfo.WaferCount + 1)
      Dim WaferFactRng As Range
      If INCLUDE_EXP_FACT_FLAG Then Set WaferFactRng = CopyWaferFact(PlotSheet)  ' 如果需要则复制晶圆参数数据
      
      Dim i: For i = 1 To myTestinfo.ParamCount
         ChartCount = ChartCount + 1
         Application.StatusBar = "创建BoxPlot Chart " & ChartCount
         Dim WaferIndex: For WaferIndex = 0 To myTestinfo.WaferCount
            If WaferIndex = 0 Then
               .Cells(WaferIndex + 1, 1) = "Wafer"  ' 设置表头行
               .Cells(WaferIndex + 1, 2) = "#N/A"
               .Cells(WaferIndex + 1, 3) = "#N/A"
               .Cells(WaferIndex + 1, 4) = "#N/A"
               .Cells(WaferIndex + 1, 5) = "#N/A"
               .Cells(WaferIndex + 1, 6) = "#N/A"
            Else
               .Cells(WaferIndex + 1, 1) = myTestinfo.Wafers(WaferIndex).WaferId  ' 晶圆ID
               .Cells(WaferIndex + 1, 2) = myBoxPlotChartParam(WaferIndex, i).Q1  ' 第一四分位
               .Cells(WaferIndex + 1, 3) = myBoxPlotChartParam(WaferIndex, i).PlotMax  ' 上限值
               .Cells(WaferIndex + 1, 4) = myBoxPlotChartParam(WaferIndex, i).PlotMin  ' 下限值
               .Cells(WaferIndex + 1, 5) = myBoxPlotChartParam(WaferIndex, i).Q2  ' 中位数
               .Cells(WaferIndex + 1, 6) = myBoxPlotChartParam(WaferIndex, i).Q3  ' 第三四分位
            End If
         Next
         Dim tmpBoxPlotChart As Chart: Set tmpBoxPlotChart = .ChartObjects(1).Chart
         With tmpBoxPlotChart
            .ChartTitle.Text = myTestinfo.Params(i).Id & _
               "[" & myTestinfo.Params(i).Unit & "]" & _
               "@" & myTestinfo.Params(i).TestCond(LBound(myTestinfo.Params(i).TestCond)) & _
               " BoxPlot Chart"  ' 设置图表标题
            Dim j: For j = 1 To 5
               .SeriesCollection(j).Name = "p" & j  ' 设置系列名
               .SeriesCollection(j).Values = WaferRange.Offset(0, j).Value  ' 设置数据源
            Next
         End With
         BOXPLOT_SHEET.ChartObjects(1).Copy
         PlotSheet.Paste  ' 粘贴图表到结果表
         Dim myChartObject As ChartObject: Set myChartObject = PlotSheet.ChartObjects(PlotSheet.ChartObjects.Count)
         With myChartObject
            .Left = 10  ' 设置左边距
            .Top = 10 + (ChartCount - 1) * (.Height + 20)  ' 设置上边距
            If (Not WaferFactRng Is Nothing) And WaferQtyOkFlag Then
               For j = 1 To 5
                  .Chart.SeriesCollection(j).Xvalues = WaferFactRng  ' 设置图表的X轴标签
               Next
            Else
            End If
            Dim OrignHeight: OrignHeight = myChartObject.Chart.PlotArea.Height
            myChartObject.Chart.PlotArea.Height = OrignHeight - 200  ' 临时调整绘图区高度以刷新
            myChartObject.Chart.PlotArea.Height = OrignHeight  ' 恢复绘图区高度，解决图表显示问题
         End With
      Next
   End With
End Function

' 计算所有晶圆参数的箱线图统计值
Public Function CalBoxChart(myTestinfo As CPLot) As BoxPlotChartParam()
   Dim Ret() As BoxPlotChartParam: ReDim Ret(1 To myTestinfo.WaferCount, 1 To myTestinfo.ParamCount)
   Dim WaferIndex: For WaferIndex = 1 To myTestinfo.WaferCount
      Application.StatusBar = "BoxPlot计算中..." & myTestinfo.Wafers(WaferIndex).WaferId
      If myTestinfo.Wafers(WaferIndex).ChipCount > 0 Then
         Dim i: For i = 1 To myTestinfo.ParamCount
            Dim myData: myData = myTestinfo.Wafers(WaferIndex).ChipDatas(i)
            Ret(WaferIndex, i) = CalBoxPlotChartParam(myData)  ' 计算每个参数的箱线图统计值
         Next
      End If
   Next
   CalBoxChart = Ret
End Function

' 计算单个参数的箱线图统计值
Private Function CalBoxPlotChartParam(myData) As BoxPlotChartParam
   Dim Ret As BoxPlotChartParam
   With WorksheetFunction
      Dim Q1: Q1 = .Quartile(myData, 1)  ' 计算第一四分位
      Dim Q2: Q2 = .Quartile(myData, 2)  ' 计算中位数
      Dim Q3: Q3 = .Quartile(myData, 3)  ' 计算第三四分位
      Dim MinVal: MinVal = .Min(myData)  ' 最小值
      Dim MaxVal: MaxVal = .Max(myData)  ' 最大值
      Dim IR: IR = 1.5 * (Q3 - Q1)  ' 四分位距的1.5倍
      Dim MinIR: MinIR = Q1 - IR  ' 下限值
      Dim MaxIR: MaxIR = Q3 + IR  ' 上限值
      Dim PlotMin: PlotMin = IIf(MinVal < MinIR, MinIR, MinVal)  ' 确定箱线图下限（去除异常值）
      Dim PlotMax: PlotMax = IIf(MaxVal > MaxIR, MaxIR, MaxVal)  ' 确定箱线图上限（去除异常值）
   End With
   With Ret
      .Q1 = Q1
      .Q2 = Q2
      .Q3 = Q3
      .PlotMax = PlotMax
      .PlotMin = PlotMin
   End With
   CalBoxPlotChartParam = Ret
End Function
