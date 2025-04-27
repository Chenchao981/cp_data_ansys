Attribute VB_Name = "参数数值颜色图"
Option Explicit

' --- 全局常量定义 ---
' 定义绘制在 Excel 工作表上的 MAP 图的大致高度和宽度 (单位：磅?)
Public Const gMapHeight = 355 * 0.6
Public Const gMapWidth = 315 * 0.6

' 计算每个参数的颜色刻度分界点
' TestVal: 包含所有 Wafer 所有参数测试值的 Range 对象 (来自 "Data" 工作表)
' 返回值: 二维数组 Ret(1 To 7, 1 To ParamCount)，每列存储一个参数的 7 个颜色分界点
' 分界点计算方法基于四分位数 (Q1, Q2, Q3) 和四分位距 (IQR = Q3 - Q1)
' 7 个点通常对应: Q1-3*IQR, Q1-1.5*IQR, Q1, Q2, Q3, Q3+1.5*IQR, Q3+3*IQR
Public Function ColorPointSetup(TestVal As Range)
   On Error Resume Next
   Dim x: x = TestVal.Value ' 将 Range 数据读入数组以提高性能
   If Err.Number <> 0 Or Not IsArray(x) Then Exit Function
   On Error GoTo 0
   
   Dim ParamCount As Long: ParamCount = UBound(x, 2)
   Dim Ret: ReDim Ret(1 To 7, 1 To ParamCount)
   Dim i As Long
   For i = 1 To ParamCount
      Dim myDataCol As Range: Set myDataCol = TestVal.Columns(i)
      
      On Error Resume Next ' 忽略 WorksheetFunction 可能出现的错误 (如数据为空或非数值)
      Dim Q1: Q1 = WorksheetFunction.Quartile_Inc(myDataCol, 1) ' 使用 Quartile_Inc (兼容 Excel 2010+)
      Dim Q2: Q2 = WorksheetFunction.Median(myDataCol)
      Dim Q3: Q3 = WorksheetFunction.Quartile_Inc(myDataCol, 3)
      Dim MaxVal: MaxVal = WorksheetFunction.Max(myDataCol)
      Dim MinVal: MinVal = WorksheetFunction.Min(myDataCol)
      If Err.Number <> 0 Then GoTo SkipParam ' 如果计算统计量出错，则跳过此参数
      On Error GoTo 0
      
      Dim IR As Double
      ' 检查 Q1 和 Q3 是否有效且不同
      If IsNumeric(Q1) And IsNumeric(Q3) And Q1 <> Q3 Then
         IR = Q3 - Q1
         Ret(1, i) = Q1 - 3 * IR
         Ret(2, i) = Q1 - 1.5 * IR
         Ret(3, i) = Q1
         Ret(4, i) = Q2
         Ret(5, i) = Q3
         Ret(6, i) = Q3 + 1.5 * IR
         Ret(7, i) = Q3 + 3 * IR
         ' 可选：将极端值限制在 Min/Max 范围内 (当前代码已注释掉)
         ' If Ret(1, i) < MinVal Then Ret(1, i) = MinVal
         ' If Ret(2, i) < MinVal Then Ret(2, i) = MinVal
         ' If Ret(6, i) > MaxVal Then Ret(6, i) = MaxVal
         ' If Ret(7, i) > MaxVal Then Ret(7, i) = MaxVal
      Else ' 如果 Q1 = Q3 或无效，则使用 Min/Max 和 Q1/Q3 的加权平均来定义部分点
         Ret(1, i) = MinVal
         Ret(2, i) = IIf(IsNumeric(Q1), Q1 * 0.8 + MinVal * 0.2, MinVal) ' 简单线性插值
         Ret(3, i) = Q1
         Ret(4, i) = Q2
         Ret(5, i) = Q3
         Ret(6, i) = IIf(IsNumeric(Q3), Q3 * 0.8 + MaxVal * 0.2, MaxVal)
         Ret(7, i) = MaxVal
      End If
SkipParam:
   Next i
   
   ColorPointSetup = Ret
End Function

' 绘制所有参数的数值颜色图到 "ParamColorChart" 工作表，并将颜色刻度添加到 PPT 中
Public Sub PlotDataColor(w As Workbook, myTestinfo As CPLot, myPPT As Object, myColorPoint)
   Dim PlotSheet As Worksheet: Set PlotSheet = w.Worksheets("ParamColorChart")
   Dim h As Long, WaferRowOffset As Long
   Dim WaferIndex As Long
   
   If Not IsArray(myColorPoint) Then
       gShow.ErrAlarm "颜色分界点数据无效，无法绘制参数数值颜色图。"
       Exit Sub
   End If
   
   For WaferIndex = 1 To myTestinfo.WaferCount
      With myTestinfo.Wafers(WaferIndex)
         If .ChipCount = 0 Then GoTo NextWafer ' 跳过没有 Chip 的 Wafer
         Dim MapGridWidth As Long: MapGridWidth = .Width + 2 ' 每个 Map 在 Excel 中占用的宽度 (列数)
         Application.StatusBar = "绘制参数数值颜色图..." & .WaferId & "#"
         
         Dim j As Long: For j = 1 To myTestinfo.ParamCount
            ' 计算当前 Map 在 Excel 中的起始单元格
            Dim StartCell As Range: Set StartCell = PlotSheet.Range("b2").Offset(WaferRowOffset, MapGridWidth * (j - 1))
            StartCell.Offset(-1, -1) = .WaferId & "#" ' 标注 Wafer ID
            
            ' 获取当前参数的颜色分界点
            Dim ParamColorPoint
            On Error Resume Next
            ParamColorPoint = WorksheetFunction.Index(myColorPoint, 0, j) ' 从 myColorPoint 数组提取第 j 列
            If Err.Number <> 0 Then GoTo SkipParamPlot ' 如果提取失败，跳过此参数
            ParamColorPoint = WorksheetFunction.Transpose(ParamColorPoint) ' 转置为一维数组
            On Error GoTo 0
            
            ' 构建 Map 标题
            Dim myTitle As String
            myTitle = .WaferId & "#" & myTestinfo.Params(j).Id
            StartCell.Offset(-1, Int(MapGridWidth * 0.35)) = myTitle ' 在 Map 上方大致居中显示标题
            
            ' 绘制当前参数的颜色 Map 到 Excel，并添加到 PPT
            h = PlotParamColorChart(StartCell, myTestinfo.Wafers(WaferIndex), j, ParamColorPoint, myPPT) + 2 ' 获取绘制高度并加 2 行间距
            
            ' 仅在处理第一个 Wafer 时，将颜色刻度添加到对应的 PPT 参数幻灯片
            If WaferIndex = 1 Then AddScaleColor myPPT.slides(j + 2), ParamColorPoint
SkipParamPlot:
         Next j
         WaferRowOffset = WaferRowOffset + h ' 更新下一行 Wafer Map 的起始行偏移量
      End With
NextWafer:
   Next WaferIndex
   
   PlotSheet.Activate
   ActiveWindow.DisplayGridlines = False
  
End Sub

' 绘制单个参数的颜色 Map 到 Excel，并添加到 PPT
Private Function PlotParamColorChart(StartCell As Range, myWaferInfo As CPWafer, ParamIndex, ParamColorPoint, myPPT As Object) As Long
   Dim x, Y, ParamData
   ParamData = myWaferInfo.ChipDatas(ParamIndex) ' 获取当前参数的数据
   x = myWaferInfo.x
   Y = myWaferInfo.Y
   
   ' 检查数据有效性
   If Not IsArray(x) Or Not IsArray(Y) Or Not IsArray(ParamData) Then PlotParamColorChart = 0: Exit Function
   If UBound(x) <> UBound(Y) Or UBound(x) <> UBound(ParamData) Then PlotParamColorChart = 0: Exit Function
   If myWaferInfo.ChipCount = 0 Then PlotParamColorChart = 0: Exit Function
   
   On Error Resume Next
   Dim MinX: MinX = Application.WorksheetFunction.Min(x)
   Dim MaxX: MaxX = Application.WorksheetFunction.Max(x)
   Dim MinY: MinY = Application.WorksheetFunction.Min(Y)
   Dim MaxY: MaxY = Application.WorksheetFunction.Max(Y)
   If Err.Number <> 0 Then PlotParamColorChart = 0: Exit Function
   On Error GoTo 0
   
   ' 设置 Excel Map 单元格大小
   SetMapCellSize StartCell, MinY, MaxY, MinX, MaxX
   
   ' 创建二维数组 d 并填充参数值 (X 轴翻转)
   Dim MapHeight As Long: MapHeight = MaxY - MinY
   Dim MapWidth As Long: MapWidth = MaxX - MinX
   Dim d: ReDim d(0 To MapHeight, 0 To MapWidth)
   Dim i As Long: For i = 1 To UBound(x)
      Dim xx As Integer: xx = x(i, 1) - MinX
      Dim yy As Integer: yy = Y(i, 1) - MinY
      If yy >= 0 And yy <= MapHeight And xx >= 0 And xx <= MapWidth Then
         d(yy, MaxX - x(i, 1)) = ParamData(i, 1)
      End If
   Next
   
   ' 将数据写入 Excel 并应用条件格式
   Dim MapRng As Range: Set MapRng = StartCell.Resize(MapHeight + 1, MapWidth + 1)
   MapRng.Value = d
   SetFormatCondtions MapRng, ParamColorPoint ' 应用颜色刻度条件格式
   
   ' 将 Excel Map 添加到对应的 PPT 参数幻灯片 (幻灯片索引 = 参数索引 + 2)
   AddMap MapRng, myPPT.slides(2 + ParamIndex), CInt(myWaferInfo.WaferId)
   
   PlotParamColorChart = MapHeight + 1 ' 返回绘制的行数
End Function

' 在 PPT 幻灯片上添加颜色刻度图例
Private Function AddScaleColor(mySlide As Object, ParamColorPoint)
   On Error Resume Next
   ' 1. 从 DATA_COLOR_SHEET 复制预定义的颜色条图片 ("Picture 1")
   DATA_COLOR_SHEET.Shapes("Picture 1").CopyPicture
   If Err.Number <> 0 Then
       gShow.ErrAlarm "无法复制颜色刻度图片 (来自 DATA_COLOR_SHEET)。"
       Exit Function
   End If
   
   ' 2. 粘贴颜色条图片到 PPT 幻灯片
   Dim myShape As Object: Set myShape = mySlide.Shapes.Paste
   If Err.Number <> 0 Or myShape Is Nothing Then
       gShow.ErrAlarm "无法粘贴颜色刻度图片到幻灯片 " & mySlide.SlideIndex & "。"
       Exit Function
   End If
   
   ' 3. 调整颜色条的位置 (大致垂直居中)
   With myShape
      .Left = 40
      .Top = 40 + (500 - .Height) / 2 ' 500 可能是幻灯片内容区域的估计高度?
   End With
   
   ' 4. 在颜色条旁边添加表示极端值颜色的小矩形 (颜色来自 DATA_COLOR_SHEET)
   ' (这些矩形的颜色和位置似乎是硬编码的，对应颜色刻度的两端额外颜色)
   Dim RectShape As Object
   Set RectShape = mySlide.Shapes.AddShape(msoShapeRectangle, 40, myShape.Top - 20, 10, 15)
   If Not RectShape Is Nothing Then
       RectShape.Fill.ForeColor.RGB = DATA_COLOR_SHEET.Range("b3").Interior.Color
       RectShape.Line.Visible = False
   End If
   Set RectShape = mySlide.Shapes.AddShape(msoShapeRectangle, 40, myShape.Top - 40, 10, 15)
   If Not RectShape Is Nothing Then
       RectShape.Fill.ForeColor.RGB = DATA_COLOR_SHEET.Range("b2").Interior.Color
       RectShape.Line.Visible = False
   End If
   Set RectShape = mySlide.Shapes.AddShape(msoShapeRectangle, 40, myShape.Top + myShape.Height + 5, 10, 15)
   If Not RectShape Is Nothing Then
       RectShape.Fill.ForeColor.RGB = DATA_COLOR_SHEET.Range("b7").Interior.Color
       RectShape.Line.Visible = False
   End If
   Set RectShape = mySlide.Shapes.AddShape(msoShapeRectangle, 40, myShape.Top + myShape.Height + 25, 10, 15)
   If Not RectShape Is Nothing Then
       RectShape.Fill.ForeColor.RGB = DATA_COLOR_SHEET.Range("b8").Interior.Color
       RectShape.Line.Visible = False
   End If
   
   ' 5. 在颜色条和矩形旁边添加数值标签 (显示对应的颜色分界点值)
   AddScaleLabel mySlide, myShape.Top - 20, ParamColorPoint(7) ' 对应 b3 颜色 (Q3+3IQR)
   AddScaleLabel mySlide, myShape.Top, ParamColorPoint(6)      ' 颜色条顶端 (Q3+1.5IQR)
   AddScaleLabel mySlide, myShape.Top + myShape.Height / 2, ParamColorPoint(4) ' 颜色条中间 (Q2)
   AddScaleLabel mySlide, myShape.Top + myShape.Height, ParamColorPoint(2) ' 颜色条底端 (Q1-1.5IQR)
   AddScaleLabel mySlide, myShape.Top + myShape.Height + 20, ParamColorPoint(1) ' 对应 b7 颜色 (Q1-3IQR)
   ' 注意：这里标签对应的 ParamColorPoint 索引与颜色设置的逻辑可能需要仔细核对
   On Error GoTo 0
End Function

' 在 PPT 幻灯片指定垂直位置 (Top) 添加数值标签
Private Function AddScaleLabel(mySlide As Object, Top As Single, info As Variant)
   If IsEmpty(info) Or Not IsNumeric(info) Then Exit Function ' 如果值无效则不添加标签
   On Error Resume Next
   With mySlide.Shapes.AddLabel(msoTextOrientationHorizontal, 1, Top - 10, 80, 50)
      ' 格式化数值显示 (使用 ChangeDisplayNum 函数)
      .TextFrame.TextRange.Text = Right(Space(6) & ChangeDisplayNum(info), 6) & "->"
      .Line.Visible = False
      .TextEffect.FontSize = 10
   End With
   On Error GoTo 0
End Function

' 将数值转换为带单位后缀 (m, u, n, p) 的字符串，并限制位数
Private Function ChangeDisplayNum(info) As String
   If IsEmpty(info) Or Not IsNumeric(info) Then ChangeDisplayNum = "": Exit Function
   Dim Ret As String
   Dim AbsVal: AbsVal = Abs(CDbl(info))
   
   Select Case AbsVal
   Case 0: Ret = "0"
   Case Is >= 1: Ret = SetNumberQty(info)
   Case Is >= 0.001: Ret = SetNumberQty(Round(info * 1000, 3)) & "m"
   Case Is >= 0.000001: Ret = SetNumberQty(Round(info * 1000000#, 3)) & "u"
   Case Is >= 0.000000001: Ret = SetNumberQty(Round(info * 1000000000#, 3)) & "n"
   Case Is > 0: Ret = SetNumberQty(Round(info * 1000000000000#, 3)) & "p"
   Case Else: Ret = SetNumberQty(info) ' 处理负数或未覆盖的情况
   End Select
   ChangeDisplayNum = Ret
End Function

' 格式化数字字符串，限制总位数（似乎是包括小数点和小数部分的固定位数格式?）
Public Function SetNumberQty(info) As String
   Const N As Integer = 4 ' 目标总位数?
   Dim Ret As String
   Ret = CStr(info)
   
   ' 处理小数点开头的数字
   If Left(Ret, 1) = "." Then
      Ret = "0" & Left(Ret, N) ' 保留小数点后 N-1 位?
   ' 处理负数且小数点开头
   ElseIf Left(Ret, 2) = "-." Then
      Ret = "-0." & Mid(Ret, 3, N - 2) ' 保留小数点后 N-2 位?
   Else
      Dim Pos As Integer: Pos = InStr(Ret, ".")
      If Pos > 0 Then ' 如果有小数点
         ' 根据整数部分位数调整小数位数，使得总有效数字（或总长度？）接近 N
         Dim DecimalPlaces As Integer: DecimalPlaces = N - Pos + IIf(Left(Ret, 1) = "-", 0, 1) ' 计算保留的小数位数
         If DecimalPlaces < 0 Then DecimalPlaces = 0
         Ret = CStr(Round(info, DecimalPlaces))
      'Else ' 如果是整数，可能需要限制长度或补零，当前代码未处理
      End If
   End If
   SetNumberQty = Ret
End Function

' (此函数似乎未被调用)
' 创建一个单元格 Interior 对象的二维数组 (用途不明)
Private Function CreateCellArray(x, Y, MinX As Integer, MinY As Integer, StartCell As Range, Result() As Interior)
   With StartCell
      Dim i As Long: For i = 1 To UBound(x)
         Dim xx As Integer: xx = x(i, 1) - MinX
         Dim yy As Integer: yy = Y(i, 1) - MinY
         If yy >= LBound(Result, 1) And yy <= UBound(Result, 1) And xx >= LBound(Result, 2) And xx <= UBound(Result, 2) Then
             Set Result(yy, xx) = .Offset(yy, xx).Interior
         End If
      Next
   End With
End Function

' 重复定义：设置 Excel Map 单元格大小 (与 绘制MAP图.bas 中的函数重复)
Private Sub SetMapCellSize(StartCell As Range, Min_Py, Max_Py, Min_Px, Max_Px)
   Dim MapCellHeight As Double, MapCellWidth As Double
   Dim HeightFactor As Long: HeightFactor = Max_Py - Min_Py + 1
   Dim WidthFactor As Long: WidthFactor = Max_Px - Min_Px + 1
   
   If HeightFactor <= 0 Or WidthFactor <= 0 Then Exit Sub
   
   MapCellHeight = gMapHeight / HeightFactor
   MapCellWidth = 0.125 * gMapWidth / WidthFactor
   
   If MapCellHeight <= 0 Then MapCellHeight = 1
   If MapCellWidth <= 0 Then MapCellWidth = 1
   
   On Error Resume Next
   With StartCell.Resize(HeightFactor, WidthFactor)
      .ColumnWidth = MapCellWidth
      .RowHeight = MapCellHeight
   End With
   On Error GoTo 0
End Sub
   
' 将 Excel 的 Long 类型颜色值转换为 RGB 数组
Public Function CLng2RGB(x As Long)
   Dim R As Long, G As Long, B As Long
   R = x Mod 256
   G = (x \ 256) Mod 256
   B = (x \ 65536) Mod 256
   CLng2RGB = Array(R, G, B)
End Function
