Attribute VB_Name = "合并到ppt中"
Option Explicit

' 全局变量，用途不明，可能用于计时?
Dim myTimer

' 保存生成的 PPT 文件
' myPPT: PowerPoint Presentation 对象
' Lot: Lot 名称，用于构建文件名
Private Function SaveResultPPT(myPPT As Object, Lot) As String
   Dim mySaveFileName As String
   Dim myPath As String
   myPath = ThisWorkbook.Path & "\整理后的MAP报告\" ' 定义保存路径
   If Dir(myPath, vbDirectory) = "" Then MkDir myPath ' 如果路径不存在则创建
   mySaveFileName = myPath & Lot & ".pptm" ' 构建完整文件名 (保存为启用宏的演示文稿)
   
   On Error Resume Next ' 忽略删除和保存时可能发生的错误
   If Dir(mySaveFileName) <> "" Then Kill mySaveFileName ' 如果文件已存在则删除
   myPPT.SaveAs mySaveFileName, ppSaveAsPresForReview ' 保存 PPT (PresForReview格式? 通常是ppSaveAsDefault或ppSaveAsOpenXMLPresentation)
   If Err.Number <> 0 Then
       gShow.ErrAlarm "保存 PPT 文件失败: " & mySaveFileName & vbCrLf & Err.Description
       SaveResultPPT = ""
   Else
       SaveResultPPT = mySaveFileName
   End If
   On Error GoTo 0
End Function

' 为每个参数在 PPT 中创建一张幻灯片 (通过复制模板幻灯片实现)
Private Function CreateParamSlides(myTestinfo As CPLot, myPPT As Object)
   On Error Resume Next
   Dim TemplateSlide As Object: Set TemplateSlide = myPPT.slides(2) ' 假设第 2 张是模板幻灯片
   If TemplateSlide Is Nothing Then
       gShow.ErrAlarm "无法找到 PPT 模板幻灯片 (第 2 张)。"
       Exit Function
   End If
   
   With myTestinfo
      Dim i: For i = 1 To .ParamCount
         ' 复制模板幻灯片，新幻灯片会插入到模板之后
         Dim NewSlideIndex As Long: NewSlideIndex = TemplateSlide.Duplicate.SlideIndex
         ' 将新复制的幻灯片移动到最后 (可选，当前逻辑是按顺序插入)
         ' myPPT.Slides(NewSlideIndex).MoveTo myPPT.Slides.Count
      Next
      
      ' 为新创建的参数幻灯片 (从第 3 张开始) 设置标题
      For i = 1 To .ParamCount
         If i + 2 <= myPPT.Slides.Count Then
             Dim mySlide As Object: Set mySlide = myPPT.slides(i + 2)
             With .Params(i)
                AddTitle mySlide, .Id & "[" & .Unit & "] Map" ' 添加标题，例如 "Param1[V] Map"
             End With
         Else
             gShow.ErrAlarm "创建参数幻灯片时索引超出范围: " & i + 2
             Exit For
         End If
      Next
   End With
   On Error GoTo 0
End Function

' 创建并初始化 PPT 结果文件
Public Function CreateResultPPT(myTestinfo As CPLot) As Object
   Dim pptApp As Object
   On Error Resume Next
   Set pptApp = GetObject(, "Powerpoint.Application") ' 尝试获取已运行的 PowerPoint 实例
   If Err.Number <> 0 Then
       Set pptApp = CreateObject("Powerpoint.Application") ' 如果未运行，则创建新实例
   End If
   On Error GoTo 0
   If pptApp Is Nothing Then
       gShow.ErrStop "无法创建或连接 PowerPoint 应用程序。"
       Set CreateResultPPT = Nothing: Exit Function
   End If
   
   pptApp.Visible = True ' 使 PowerPoint 应用程序可见
   
   Dim myPPT As Object
   Dim TemplatePath As String: TemplatePath = ThisWorkbook.Path & "\WaferMap.potm" ' 模板文件路径
   If Dir(TemplatePath) = "" Then
       gShow.ErrStop "找不到 PowerPoint 模板文件: " & TemplatePath
       Set CreateResultPPT = Nothing: Exit Function
   End If
   
   On Error Resume Next
   Set myPPT = pptApp.Presentations.Open(TemplatePath)
   If Err.Number <> 0 Or myPPT Is Nothing Then
       gShow.ErrStop "打开 PowerPoint 模板文件失败: " & TemplatePath & vbCrLf & Err.Description
       Set CreateResultPPT = Nothing: Exit Function
   End If
   On Error GoTo 0
   
   ' 1. 添加 PPT 首页标题
   AddTitle2PPT myPPT, myTestinfo.Product
   ' 2. 添加 Bin Map 幻灯片标题 (假设模板第2页用于 Bin Map)
   AddBinMapSlide myPPT
   ' 3. 根据参数数量复制模板幻灯片并设置标题
   CreateParamSlides myTestinfo, myPPT
   
   ' 4. 保存 PPT 文件 (注：这里提前保存，后续 AddMap 会继续修改)
   ' SaveResultPPT myPPT, myTestinfo.Product ' 建议移到所有内容添加完成后再保存
   
   Set CreateResultPPT = myPPT
End Function

' (此函数似乎未被调用，且功能不完整)
' 为添加到 PPT 的 Wafer Map 图片添加宏动作 (鼠标点击时运行 "ClickWafer" + WaferId 宏)
Private Function AddAnimation2Map(mySlide As Object, WaferMap As Object, WaferId)
   ' 注意: 此功能要求保存为 .pptm 格式，并且接收方允许执行宏
   On Error Resume Next
   With WaferMap.ActionSettings(ppMouseClick)
      .Action = ppActionRunMacro
      .Run = "ClickWafer" & WaferId
   End With
   On Error GoTo 0
End Function

' 在指定的 PPT 幻灯片中查找预设的 5x5 表格 (用于定位 Wafer Map 的位置)
Private Function GetSlideWaferTable(mySlide As Object) As Object
   Dim Ret As Object
   Dim myShape As Object
   On Error Resume Next
   For Each myShape In mySlide.Shapes
      If myShape.HasTable Then
         Dim myTable As Object: Set myTable = myShape.Table
         If myTable.Columns.Count = 5 And myTable.Rows.Count = 5 Then
            Set Ret = myTable: Exit For
         End If
      End If
   Next
   On Error GoTo 0
   Set GetSlideWaferTable = Ret
End Function

' 根据 WaferId 在 5x5 表格中计算对应的单元格 Shape 对象
Private Function GetWaferCell(myTable As Object, WaferId) As Object
   If myTable Is Nothing Then Exit Function
   ' WaferId 从 1 开始计数
   Dim myRow As Long: myRow = (WaferId - 1) \ 5 + 1 ' 计算行号 (1-based)
   Dim myCol As Long: myCol = (WaferId - 1) Mod 5 + 1 ' 计算列号 (1-based)
   
   On Error Resume Next
   Set GetWaferCell = myTable.Cell(myRow, myCol).Shape
   On Error GoTo 0
End Function

' 将 Excel 中的 Map 范围 (MapRng) 复制为图片，粘贴到指定 PPT 幻灯片 (mySlide) 的对应 Wafer 位置
Public Function AddMap(MapRng As Range, mySlide As Object, WaferId) As Object
   Dim Ret As Object
   ' 1. 在幻灯片中查找 5x5 表格
   Dim SlideTable As Object: Set SlideTable = GetSlideWaferTable(mySlide)
   If SlideTable Is Nothing Then
       gShow.ErrAlarm "在幻灯片 " & mySlide.SlideIndex & " 中未找到 5x5 Wafer 表格。"
       Exit Function
   End If
   ' 2. 根据 WaferId 获取目标单元格
   Dim myCell As Object: Set myCell = GetWaferCell(SlideTable, WaferId)
   If myCell Is Nothing Then
       gShow.ErrAlarm "在幻灯片 " & mySlide.SlideIndex & " 的表格中未找到 Wafer " & WaferId & " 的单元格。"
       Exit Function
   End If
   
   Application.ScreenUpdating = True ' 确保 Excel 界面更新以正确复制图片
   On Error Resume Next
   ' 3. 将 Excel 范围复制为图片 (xlScreen, xlBitmap)
   MapRng.CopyPicture Appearance:=xlScreen, Format:=xlBitmap
   If Err.Number <> 0 Then
       gShow.ErrAlarm "复制 Wafer Map 图片失败 (Wafer " & WaferId & ")。"
       Exit Function
   End If
   
   ' 4. 将图片粘贴到 PPT 幻灯片
   Dim myMapShape As Object: Set myMapShape = mySlide.Shapes.Paste
   If Err.Number <> 0 Or myMapShape Is Nothing Then
       gShow.ErrAlarm "粘贴 Wafer Map 图片失败 (Wafer " & WaferId & ") 到幻灯片 " & mySlide.SlideIndex & "。"
       Application.CutCopyMode = False
       Exit Function
   End If
   Application.CutCopyMode = False ' 清除剪贴板
   
   ' 5. 调整粘贴的图片大小和位置，使其适应目标单元格
   With myMapShape
      .Name = "Map" & WaferId
      ' 按比例缩放以适应单元格宽度或高度，并居中
      Dim CellWidth As Single: CellWidth = myCell.Width - 5 ' 留出边距
      Dim CellHeight As Single: CellHeight = myCell.Height - 5
      Dim Ratio As Single
      If (.Width / CellWidth) > (.Height / CellHeight) Then
          Ratio = CellWidth / .Width
      Else
          Ratio = CellHeight / .Height
      End If
      .ScaleWidth Ratio, msoTrue
      .ScaleHeight Ratio, msoTrue
      .Left = myCell.Left + (myCell.Width - .Width) / 2
      .Top = myCell.Top + (myCell.Height - .Height) / 2
   End With
   
   ' 6. (可选) 添加宏动作
   ' AddAnimation2Map mySlide, myMapShape, WaferId
   
   Set AddMap = myMapShape ' 返回粘贴的 Shape 对象
   On Error GoTo 0
End Function

' 设置 PPT 首页 (第 1 张) 的标题和副标题
Private Function AddTitle2PPT(myPPT As Object, Lot)
   On Error Resume Next
   With myPPT.slides(1)
      If .Shapes.Count >= 1 Then .Shapes(1).TextFrame.TextRange.Text = Lot & " MAP Review"
      If .Shapes.Count >= 2 Then .Shapes(2).TextFrame.TextRange.Text = Application.UserName & vbCrLf & Format(Date, "yyyy-mm-dd")
   End With
   On Error GoTo 0
End Function

' 为 Bin Map 幻灯片 (第 2 张) 添加标题
Private Function AddBinMapSlide(myPPT As Object)
   On Error Resume Next
   Dim mySlide As Object: Set mySlide = myPPT.slides(2)
   If Not mySlide Is Nothing Then
       AddTitle mySlide, "Bin Map"
   End If
   On Error GoTo 0
End Function

' 在指定幻灯片添加一个标签作为标题
Private Function AddTitle(mySlide As Object, info As String)
   On Error Resume Next
   Dim myTitle As Object
   ' 查找是否已存在标题占位符
   For Each myTitle In mySlide.Shapes
       If myTitle.Type = msoPlaceholder Then
           If myTitle.PlaceholderFormat.Type = ppPlaceholderTitle Or myTitle.PlaceholderFormat.Type = ppPlaceholderCenterTitle Then
               myTitle.TextFrame.TextRange.Text = info
               Exit Function ' 找到并设置后退出
           End If
       End If
   Next
   ' 如果没有找到标题占位符，则添加一个新的标签
   Set myTitle = mySlide.Shapes.AddLabel(msoTextOrientationHorizontal, Left:=10, Top:=10, Width:=mySlide.Master.Width - 20, Height:=50)
   If Not myTitle Is Nothing Then
       myTitle.TextFrame.TextRange.Text = info
       myTitle.TextFrame.TextRange.Font.Size = 24 ' 设置字体大小
       myTitle.TextFrame.TextRange.Font.Bold = msoTrue
   End If
   On Error GoTo 0
End Function

' (此函数似乎未被调用)
' 在指定幻灯片添加一个 5x5 的表格，并填充数字 1-25
Private Function AddWaferTable2Slide(mySlide As Object)
   Dim NumRows As Long: NumRows = 5
   Dim NumColumns As Long: NumColumns = 5
   Dim Left As Single: Left = 50
   Dim Top As Single: Top = 40
   Dim Width As Single: Width = 650
   Dim Height As Single: Height = 500
   
   On Error Resume Next
   Dim myTableShape As Object: Set myTableShape = mySlide.Shapes.AddTable(NumRows, NumColumns, Left, Top, Width, Height)
   If Err.Number <> 0 Or myTableShape Is Nothing Then
       gShow.ErrAlarm "在幻灯片 " & mySlide.SlideIndex & " 添加表格失败。"
       Exit Function
   End If
   
   With myTableShape.Table
      .FirstRow = False ' 不将第一行视为标题行
      .HorizBanding = False ' 关闭水平条纹格式
      Dim i As Long, j As Long
      For i = 1 To NumRows
         For j = 1 To NumColumns
            .Cell(i, j).Shape.TextFrame.TextRange.Text = (i - 1) * NumColumns + j
            .Cell(i, j).Shape.TextFrame.HorizontalAnchor = msoAnchorCenter
            .Cell(i, j).Shape.TextFrame.VerticalAnchor = msoAnchorMiddle
         Next
      Next
   End With
   On Error GoTo 0
End Function
