Attribute VB_Name = "绘制MAP图" ' 模块名：绘制MAP图
Option Explicit

' 计算并绘制所有 Wafer 的 Bin Map 到 "Map" 工作表，并将晶圆 Map 图复制到 PPT 中
Public Sub PlotAllMap(w As Workbook, myTestinfo As CPLot, myPPT As Object)
   ' 1. 从 BIN_SETUP_SHEET 获取 Bin 颜色配置字典
   Dim BinColorDic As Object: Set BinColorDic = CreateBinColorDic(BIN_SETUP_SHEET)
   If BinColorDic Is Nothing Or BinColorDic.Count = 0 Then
       gShow.ErrAlarm "找不到有效 Bin 颜色配置 (BIN_SETUP_SHEET)，无法绘制 MAP 图"
       Exit Sub
   End If
   
   Dim MapSheet As Worksheet: Set MapSheet = w.Worksheets("Map")
   With MapSheet
      Dim StartCell As Range: Set StartCell = .Range("b2") ' MAP 图起始单元格位置
      ' 2. 遍历所有 Wafer
      Dim WaferIndex: For WaferIndex = 1 To myTestinfo.WaferCount
         Application.StatusBar = "绘制MAP图..." & myTestinfo.Wafers(WaferIndex).WaferId & "#"
         StartCell.Offset(-1, -1) = myTestinfo.Wafers(WaferIndex).WaferId & "#" ' 左上角显示 Wafer ID
         ' 3. 绘制单个 Wafer 的 Bin Map 到 MapSheet，并返回绘制的高度
         Dim h: h = PlotBinMap(StartCell, myTestinfo.Wafers(WaferIndex), BinColorDic, myPPT)
         ' 4. 计算下一个 Wafer Map 的起始位置 (向下偏移 h + 2 行)
         Set StartCell = StartCell.Offset(h + 2, 0)
      Next
      
      ' 5. 格式化 MapSheet
      .Activate
      ActiveWindow.DisplayGridlines = False
      .Columns(1).ColumnWidth = 20 ' 设置 A 列宽度
      ' 6. 将 BIN_SETUP_SHEET 中的颜色配置图例复制到 MapSheet 作为图例
      CopyColorSetup MapSheet
      .Range("a1").Activate
      If .Shapes.Count > 0 Then ' 检查是否有图形
         With .Shapes(.Shapes.Count) ' 处理最后一个图形
            .ScaleHeight 0.5, msoTrue ' 缩放高度
            .Top = 30
            .CopyPicture ' 复制图例以便粘贴到 PPT
         End With
      Else
          gShow.ErrAlarm "无法创建 Bin 颜色图例或 Map 图形"
      End If
   End With
   
   ' 7. 将颜色图例粘贴到 PPT 第 2 张幻灯片 (Bin Map Slide)
   On Error Resume Next
   Dim LegendShape As Object: Set LegendShape = myPPT.slides(2).Shapes.Paste
   If Err.Number = 0 And Not LegendShape Is Nothing Then
       LegendShape.Left = 10
       LegendShape.Top = 40
   Else
       gShow.ErrAlarm "无法将 Bin 颜色图例粘贴到 PPT中"
   End If
   On Error GoTo 0
  
End Sub

' 将 Bin 颜色配置表 (BIN_SETUP_SHEET) 复制为图片并粘贴到目标工作表 (Target)
Private Function CopyColorSetup(Target As Worksheet)
   On Error Resume Next
   BIN_SETUP_SHEET.Range("a1").CurrentRegion.CopyPicture
   If Err.Number <> 0 Then
       gShow.ErrAlarm "无法复制 Bin 颜色配置表"
       Exit Function
   End If
   Target.Paste
   If Err.Number <> 0 Then
       gShow.ErrAlarm "无法将 Bin 颜色配置表粘贴到目标工作表"
   End If
   On Error GoTo 0
End Function

' 绘制单个 Wafer 的 Bin Map 到 Excel 工作表并复制到 PPT 中
' StartCell: 在 Excel 中绘制 Map 图的起始单元格
' myWaferInfo: 单个 Wafer 的数据
' BinColorDic: Bin 颜色配置字典对象
' myPPT: PowerPoint 对象
' 返回值: 绘制的 Map 在 Excel 中的行数
Private Function PlotBinMap(StartCell As Range, myWaferInfo As CPWafer, BinColorDic As Object, myPPT As Object)
   Dim x, Y, Bin, a
   Bin = myWaferInfo.Bin
   x = myWaferInfo.x
   Y = myWaferInfo.Y
   
   ' 验证数据有效性
   If Not IsArray(x) Or Not IsArray(Y) Or Not IsArray(Bin) Then PlotBinMap = 0: Exit Function
   If UBound(x) <> UBound(Y) Or UBound(x) <> UBound(Bin) Then PlotBinMap = 0: Exit Function
   If myWaferInfo.ChipCount = 0 Then PlotBinMap = 0: Exit Function
   
   On Error Resume Next ' 计算 Min/Max 坐标范围 (容错处理)
   Dim MinX: MinX = Application.WorksheetFunction.Min(x)
   Dim MaxX: MaxX = Application.WorksheetFunction.Max(x)
   Dim MinY: MinY = Application.WorksheetFunction.Min(Y)
   Dim MaxY: MaxY = Application.WorksheetFunction.Max(Y)
   If Err.Number <> 0 Then PlotBinMap = 0: Exit Function ' 如果求解 Min/Max 出错则退出
   On Error GoTo 0
   
   ' 设置 Excel 中 Map 单元格的大小
   SetMapCellSize StartCell, MinY, MaxY, MinX, MaxX
   
   ' 创建二维数组 d，存放 Wafer 各 X, Y 坐标的数据
   Dim MapHeight As Long: MapHeight = MaxY - MinY
   Dim MapWidth As Long: MapWidth = MaxX - MinX
   Dim d: ReDim d(0 To MapHeight, 0 To MapWidth)
   
   ' 将每个 Chip 的 Bin 值填充到 d 数组矩阵中 (按照 Y 向下，X 向右)
   Dim i: For i = 1 To UBound(x)
      Dim xx As Integer: xx = x(i, 1) - MinX ' X 坐标归一化到零点 (0-based)
      Dim yy As Integer: yy = Y(i, 1) - MinY ' Y 坐标归一化到零点 (0-based)
      ' 检查坐标是否在有效范围 (防止数组越界访问异常)
      If yy >= 0 And yy <= MapHeight And xx >= 0 And xx <= MapWidth Then
          d(yy, MaxX - x(i, 1)) = Bin(i, 1) ' X坐标变换为 d(y, MaxX-x)
      End If
   Next
   
   ' 将整个 d 数组一次填充到 Excel 的 Map 区域
   Dim MapRng As Range: Set MapRng = StartCell.Resize(MapHeight + 1, MapWidth + 1)
   MapRng.Value = d
   'MapRng.Borders.LineStyle = xlContinuous ' 设置单元格边框
   
   ' 应用 Bin 颜色条件格式 (着色)
   SetBinMapFormatCondtions MapRng, BinColorDic
   
   ' 复制整个 Excel Map 区域并添加到 PPT 第 2 张幻灯片 (Bin Map Slide)
   AddMap MapRng, myPPT.slides(2), CInt(myWaferInfo.WaferId)
   
   ' 返回 Map 在 Excel 中的行数高度
   PlotBinMap = MapHeight + 1
End Function

' 从 Bin 颜色配置工作表 (ColorSetupSheet) 创建 Bin 值与颜色的对应字典
Private Function CreateBinColorDic(ColorSetupSheet As Worksheet) As Object
   Dim Ret As Object: Set Ret = CreateObject("scripting.dictionary")
   On Error Resume Next
   Dim SetupRange As Range: Set SetupRange = ColorSetupSheet.Range("a1").CurrentRegion
   If Err.Number <> 0 Or SetupRange Is Nothing Then
       Set CreateBinColorDic = Nothing: Exit Function
   End If
   
   Dim RowCount As Long: RowCount = SetupRange.Rows.Count
   If RowCount < 2 Then Set CreateBinColorDic = Nothing: Exit Function ' 如果只有表头则退出
   
   With ColorSetupSheet
      Dim i: For i = 2 To RowCount ' 从第 2 行开始处理
         Dim BinVal: BinVal = .Cells(i, 1).Value ' 第 1 列是 Bin 值
         Dim BinColor As Long: BinColor = .Cells(i, 2).Interior.Color ' 第 2 列的单元格背景色
         If Not Ret.exists(BinVal) Then ' 避免重复添加
            Ret.Add BinVal, BinColor
         End If
      Next
   End With
   On Error GoTo 0
   Set CreateBinColorDic = Ret
End Function

' 设置 Excel 单元格区域 Map 图的单元格宽高比例
Private Sub SetMapCellSize(StartCell As Range, Min_Py, Max_Py, Min_Px, Max_Px)
   Dim MapCellHeight As Double, MapCellWidth As Double
   Dim HeightFactor As Long: HeightFactor = Max_Py - Min_Py + 1
   Dim WidthFactor As Long: WidthFactor = Max_Px - Min_Px + 1
   
   If HeightFactor <= 0 Or WidthFactor <= 0 Then Exit Sub ' 无效尺寸退出
   
   MapCellHeight = gMapHeight / HeightFactor
   MapCellWidth = 0.125 * gMapWidth / WidthFactor ' 系数 0.125 用于调整宽高比，使单元格接近正方形
   
   ' 防止设置过小的值
   If MapCellHeight <= 0 Then MapCellHeight = 1
   If MapCellWidth <= 0 Then MapCellWidth = 1
   
   On Error Resume Next
   With StartCell.Resize(HeightFactor, WidthFactor)
      .ColumnWidth = MapCellWidth
      .RowHeight = MapCellHeight
   End With
   On Error GoTo 0
End Sub

