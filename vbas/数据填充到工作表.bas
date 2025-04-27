Attribute VB_Name = "数据填充到工作表"
Option Explicit

' 将一个 List (一维数组或逗号分隔字符串) 填充到指定的起始单元格 (StartCell)
' HorizontalFlag: True (默认) 则水平填充，False 则垂直填充
Public Function ListFill2Rng(StartCell As Range, _
                             toFillList, _
                             Optional HorizontalFlag As Boolean = True) As Range
   Dim myList, Result As Range
   myList = CheckList(toFillList) ' 确保输入是数组
   If Not IsArrayNotEmpty(myList) Then Exit Function ' 如果数组为空，则退出
   
   Dim ListLen As Long: ListLen = DimensionLength(myList)
   If ListLen = 0 Then Exit Function
   
   On Error Resume Next ' 忽略填充时可能发生的错误 (如单元格保护)
   If HorizontalFlag Then
      Set Result = StartCell.Resize(1, ListLen)
      Result.Value = myList ' 直接赋值填充
   Else
      Set Result = StartCell.Resize(ListLen, 1)
      Result.Value = Application.Transpose(myList) ' 垂直填充需要转置
   End If
   If Err.Number <> 0 Then Set Result = Nothing ' 如果出错，返回 Nothing
   On Error GoTo 0
   
   Set ListFill2Rng = Result
End Function

' 将一个二维数组 (DataArray) 填充到指定的起始单元格 (StartCell)
' ArrayTransPoseFlag: True 则先转置数组再填充，False (默认) 则直接填充
Public Function FillArray2Rng(StartCell As Range, _
                          DataArray, _
                          Optional ArrayTransPoseFlag As Boolean = False) As Range
   Dim Result As Range, Rows As Long, Cols As Long
   
   If GetDimension(DataArray) = 0 Then Exit Function ' 如果数组为空，则退出
   Rows = DimensionLength(DataArray, 1)
   Cols = DimensionLength(DataArray, 2)
   If Cols = 0 Then Cols = 1 ' 处理一维数组的情况，视为 N行 x 1列
   
   If Rows * Cols = 0 Then Exit Function ' 如果行数或列数为0，则退出
   
   On Error Resume Next ' 忽略填充时可能发生的错误
   If ArrayTransPoseFlag Then
      Set Result = StartCell.Resize(Cols, Rows)
      ' 检查是否需要使用 BigArrayTranspose 来避免 Transpose 的 65535 限制
      If Rows > 65535 Or Cols > 65535 Then
         Result.Value = BigArrayTranspose(DataArray)
      Else
         Result.Value = Application.Transpose(DataArray)
      End If
   Else
      Set Result = StartCell.Resize(Rows, Cols)
      Result.Value = DataArray
   End If
   If Err.Number <> 0 Then Set Result = Nothing ' 如果出错，返回 Nothing
   On Error GoTo 0
   
   Set FillArray2Rng = Result
End Function

'============= 工作表定位函数 =============

' 查找指定工作表中，从 A1 开始的当前区域 (CurrentRegion) 下方的第一个空白单元格 (A列)
Public Function SearchFirstBlankCell(toCheckSheet As Worksheet) As Range
   On Error Resume Next
   Set SearchFirstBlankCell = toCheckSheet.Cells(toCheckSheet.Range("a1").CurrentRegion.Rows.Count + 1, 1)
   On Error GoTo 0
End Function

' 获取指定工作表中，从 A1 开始的当前区域的总行数
Public Function SheetUsedRowsFromA1(toCheckSheet As Worksheet) As Long
   On Error Resume Next
   SheetUsedRowsFromA1 = toCheckSheet.Range("a1").CurrentRegion.Rows.Count
   On Error GoTo 0
End Function

' 获取指定工作表中，从 A1 开始的当前区域的总列数
Public Function SheetUsedColsFromA1(toCheckSheet As Worksheet) As Long
   On Error Resume Next
   SheetUsedColsFromA1 = toCheckSheet.Range("a1").CurrentRegion.Columns.Count
   On Error GoTo 0
End Function


' (此函数似乎未在项目中使用)
' 将数据表 (DataTable) 和表头 (HeadList) 显示在指定工作表 (ResultSheet) 或新工作簿中
Public Function DisplayInfo(DataTable, HeadList, Optional ResultSheet As Worksheet, Optional ArrayTransPoseFlag As Boolean = False)
   Dim TargetSheet As Worksheet
   If ResultSheet Is Nothing Then
      Dim w As Workbook: Set w = Workbooks.Add
      If w Is Nothing Then Exit Function ' 创建失败则退出
      Set TargetSheet = w.Worksheets(1)
   Else
      Set TargetSheet = ResultSheet
   End If
   
   On Error Resume Next
   With TargetSheet
      .Cells.ClearContents ' 清除原有内容 (谨慎操作!)
      ListFill2Rng .Range("a1"), HeadList
      FillArray2Rng .Range("a2"), DataTable, ArrayTransPoseFlag
   End With
   If Err.Number <> 0 Then
       gShow.ErrAlarm "显示信息失败: " & Err.Description
   End If
   On Error GoTo 0
End Function
