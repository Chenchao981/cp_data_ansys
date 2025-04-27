Attribute VB_Name = "MAP条件格式设置"
Option Explicit

' 为数据范围设置条件格式，用于显示不同的Bin颜色
Public Function SetBinMapFormatCondtions(DataRng As Range, BinColorDic As Object)
   With BinColorDic
      Dim myBins: myBins = .Keys     ' 获取所有Bin值
      Dim myColors: myColors = .items  ' 获取对应的颜色
   End With
   
   Dim myCondition As FormatCondition: Set myCondition = DataRng.FormatConditions.Add(xlBlanksCondition)
   myCondition.StopIfTrue = True  ' 空值条件格式
   Dim i: For i = LBound(myBins) To UBound(myBins)
      
    Set myCondition = DataRng.FormatConditions.Add(Type:=xlCellValue, Operator:=xlEqual, Formula1:="=" & myBins(i))
    myCondition.Interior.Color = myColors(i)  ' 设置Bin对应的填充颜色
    myCondition.Borders.LineStyle = xlContinuous  ' 添加边框
    Next
End Function

' 从颜色列表范围中获取颜色值
Private Function GetColorList(ColorListRng As Range) As Long()
   Dim Ret() As Long: ReDim Ret(1 To 7)
   With ColorListRng
      Dim i: For i = 1 To 7
         Ret(i) = .Cells(i, 1).Interior.Color  ' 获取单元格背景色
      Next
   End With
   GetColorList = Ret
End Function

' 为数据范围设置条件格式，基于颜色刻度点列表
Public Function SetFormatCondtions(DataRng As Range, ColorScalPointList)
   Dim x: x = ColorScalPointList
   Dim ColorList() As Long: ColorList = GetColorList(DATA_COLOR_SHEET.Range("b2:b8"))
   
   Dim myCondition As FormatCondition: Set myCondition = DataRng.FormatConditions.Add(xlBlanksCondition)
   myCondition.StopIfTrue = True  ' 空值条件格式
   
   SetLimitCondtion DataRng, x(1), ColorList(7), False  ' 小于最小值的颜色
   SetBetweenCondtion DataRng, x(2), x(1), ColorList(6)  ' 介于最小值和次小值之间的颜色
   
   SetLimitCondtion DataRng, x(7), ColorList(2)  ' 大于最大值的颜色
   SetBetweenCondtion DataRng, x(7), x(6), ColorList(1)  ' 介于最大值和次大值之间的颜色
   
   SetColorScaleType DataRng, x(2), ColorList(5), x(4), ColorList(4), x(6), ColorList(3)  ' 中间值的颜色刻度
   
End Function

' 设置颜色刻度类型条件格式
Public Function SetColorScaleType(DataRng As Range, ParamArray p())
   'ParamArray p()排列顺序,先数值,再颜色
   Dim myType: myType = (UBound(p) + 1) / 2
   If myType > 3 And myType < 2 Then
      MsgBox "SetColorScaleType参数传递个数不对:" & UBound(p) + 1, vbInformation
   Else
      Dim myCondition As ColorScale
      Set myCondition = DataRng.FormatConditions.AddColorScale(myType)
      With myCondition
         Dim i: For i = LBound(p) To UBound(p) Step 2
            SetColorScaleCriterion .ColorScaleCriteria(i / 2 + 1), p(i), p(i + 1)  ' 设置每个刻度点
         Next
      End With
   End If
End Function

' 设置颜色刻度条件标准
Private Function SetColorScaleCriterion(myColorScaleCriterion As ColorScaleCriterion, myVal, myColor)
   With myColorScaleCriterion
      .Type = xlConditionValueNumber  ' 使用数值类型
      .Value = myVal  ' 设置刻度值
      .FormatColor.Color = myColor  ' 设置颜色
   End With
End Function

' 设置介于两个值之间的条件格式
Private Function SetBetweenCondtion(DataRng As Range, HighVal, LowVal, DisplayColor)
   Dim myFormatCondition As FormatCondition
   Set myFormatCondition = DataRng.FormatConditions.Add(Type:=xlCellValue, Operator:=xlBetween, _
        Formula1:="=" & LowVal, Formula2:="=" & HighVal)
   myFormatCondition.Interior.Color = DisplayColor  ' 设置填充色
   myFormatCondition.StopIfTrue = True  ' 如果条件为真，停止评估其他条件
End Function

' 设置大于/小于指定值的条件格式
Private Function SetLimitCondtion(DataRng As Range, LimitVal, DisplayColor, Optional GreateFlag As Boolean = True)
   Dim myFormatCondition As FormatCondition
   Set myFormatCondition = DataRng.FormatConditions.Add(Type:=xlCellValue, _
        Operator:=IIf(GreateFlag, xlGreater, xlLess), _
        Formula1:="=" & LimitVal)
   myFormatCondition.Interior.Color = DisplayColor  ' 设置填充色
   myFormatCondition.StopIfTrue = True  ' 如果条件为真，停止评估其他条件
End Function

