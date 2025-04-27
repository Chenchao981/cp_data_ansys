Attribute VB_Name = "BoxPlotChart"
Option Explicit

' ?????????
Public Type BoxPlotChartParam
   Q1 As Double        ' ??????
   Q2 As Double        ' ???????????
   Q3 As Double        ' ??????
   PlotMin As Double   ' ?????????????
   PlotMax As Double   ' ?????????????
End Type

' ??????????????
Private Function CopyWaferFact(PlotSheet As Worksheet) As Range
   Dim Ret As Range
   With FACTOR_SHEET.Range("a1").CurrentRegion
      If .Rows.Count = 1 Then Exit Function  ' ??????????
      Dim x: ReDim x(1 To .Columns.Count, 1 To .Rows.Count)
      Dim i: For i = 1 To .Rows.Count
         Dim j: For j = 1 To .Columns.Count
            x(j, i) = .Cells(i, j)  ' ???????
         Next
      Next
   End With
   Set Ret = PlotSheet.Range("b2").Resize(UBound(x), UBound(x, 2))
   Ret.Value = x  ' ??????
   Set CopyWaferFact = Ret
End Function

' ??????????
Public Function PlotAllParamBoxChart(ResultBook As Workbook, myTestinfo As CPLot, WaferQtyOkFlag As Boolean)
   Dim PlotSheet As Worksheet: Set PlotSheet = ResultBook.Worksheets("BoxPlot")
   Dim myBoxPlotChartParam() As BoxPlotChartParam: myBoxPlotChartParam = CalBoxChart(myTestinfo)  ' ???????
   Dim ChartCount As Integer
   With BOXPLOT_SHEET
      Dim WaferRange As Range: Set WaferRange = .Cells(1, 1).Resize(myTestinfo.WaferCount + 1)
      Dim WaferFactRng As Range
      If INCLUDE_EXP_FACT_FLAG Then Set WaferFactRng = CopyWaferFact(PlotSheet)  ' ???????????????
      
      Dim i: For i = 1 To myTestinfo.ParamCount
         ChartCount = ChartCount + 1
         Application.StatusBar = "??BoxPlot Chart " & ChartCount
         Dim WaferIndex: For WaferIndex = 0 To myTestinfo.WaferCount
            If WaferIndex = 0 Then
               .Cells(WaferIndex + 1, 1) = "Wafer"  ' ??????
               .Cells(WaferIndex + 1, 2) = "#N/A"
               .Cells(WaferIndex + 1, 3) = "#N/A"
               .Cells(WaferIndex + 1, 4) = "#N/A"
               .Cells(WaferIndex + 1, 5) = "#N/A"
               .Cells(WaferIndex + 1, 6) = "#N/A"
            Else
               .Cells(WaferIndex + 1, 1) = myTestinfo.Wafers(WaferIndex).WaferId  ' ????
               .Cells(WaferIndex + 1, 2) = myBoxPlotChartParam(WaferIndex, i).Q1  ' ??Q1
               .Cells(WaferIndex + 1, 3) = myBoxPlotChartParam(WaferIndex, i).PlotMax  ' ??PlotMax
               .Cells(WaferIndex + 1, 4) = myBoxPlotChartParam(WaferIndex, i).PlotMin  ' ??PlotMin
               .Cells(WaferIndex + 1, 5) = myBoxPlotChartParam(WaferIndex, i).Q2  ' ??Q2?????
               .Cells(WaferIndex + 1, 6) = myBoxPlotChartParam(WaferIndex, i).Q3  ' ??Q3
            End If
         Next
         Dim tmpBoxPlotChart As Chart: Set tmpBoxPlotChart = .ChartObjects(1).Chart
         With tmpBoxPlotChart
            .ChartTitle.Text = myTestinfo.Params(i).Id & _
               "[" & myTestinfo.Params(i).Unit & "]" & _
               "@" & myTestinfo.Params(i).TestCond(LBound(myTestinfo.Params(i).TestCond)) & _
               " BoxPlot Chart"  ' ??????
            Dim j: For j = 1 To 5
               .SeriesCollection(j).Name = "p" & j  ' ??????
               .SeriesCollection(j).Values = WaferRange.Offset(0, j).Value  ' ?????
            Next
         End With
         BOXPLOT_SHEET.ChartObjects(1).Copy
         PlotSheet.Paste  ' ??????????
         Dim myChartObject As ChartObject: Set myChartObject = PlotSheet.ChartObjects(PlotSheet.ChartObjects.Count)
         With myChartObject
            .Left = 10  ' ??????
            .Top = 10 + (ChartCount - 1) * (.Height + 20)  ' ??????
            If (Not WaferFactRng Is Nothing) And WaferQtyOkFlag Then
               For j = 1 To 5
                  .Chart.SeriesCollection(j).Xvalues = WaferFactRng  ' ??????X???
               Next
            Else
            End If
            Dim OrignHeight: OrignHeight = myChartObject.Chart.PlotArea.Height
            myChartObject.Chart.PlotArea.Height = OrignHeight - 200  ' ?????????????
            myChartObject.Chart.PlotArea.Height = OrignHeight  ' ?????????????????
         End With
      Next
   End With
End Function

' ????????????????
Public Function CalBoxChart(myTestinfo As CPLot) As BoxPlotChartParam()
   Dim Ret() As BoxPlotChartParam: ReDim Ret(1 To myTestinfo.WaferCount, 1 To myTestinfo.ParamCount)
   Dim WaferIndex: For WaferIndex = 1 To myTestinfo.WaferCount
      Application.StatusBar = "BoxPlot??..." & myTestinfo.Wafers(WaferIndex).WaferId
      If myTestinfo.Wafers(WaferIndex).ChipCount > 0 Then
         Dim i: For i = 1 To myTestinfo.ParamCount
            Dim myData: myData = myTestinfo.Wafers(WaferIndex).ChipDatas(i)
            Ret(WaferIndex, i) = CalBoxPlotChartParam(myData)  ' ??????????????
         Next
      End If
   Next
   CalBoxChart = Ret
End Function

' ?????????????
Private Function CalBoxPlotChartParam(myData) As BoxPlotChartParam
   Dim Ret As BoxPlotChartParam
   With WorksheetFunction
      Dim Q1: Q1 = .Quartile(myData, 1)  ' ????????
      Dim Q2: Q2 = .Quartile(myData, 2)  ' ?????
      Dim Q3: Q3 = .Quartile(myData, 3)  ' ????????
      Dim MinVal: MinVal = .Min(myData)  ' ???
      Dim MaxVal: MaxVal = .Max(myData)  ' ???
      Dim IR: IR = 1.5 * (Q3 - Q1)  ' ?????1.5?
      Dim MinIR: MinIR = Q1 - IR  ' ???
      Dim MaxIR: MaxIR = Q3 + IR  ' ???
      Dim PlotMin: PlotMin = IIf(MinVal < MinIR, MinIR, MinVal)  ' ????????????
      Dim PlotMax: PlotMax = IIf(MaxVal > MaxIR, MaxIR, MaxVal)  ' ????????????
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
