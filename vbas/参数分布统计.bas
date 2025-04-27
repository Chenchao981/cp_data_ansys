Attribute VB_Name = "参数分布统计"
Option Explicit

' 计算每个 Wafer 每个参数的统计信息 (Avg, Std, Median, RobustStd)，并将结果填充到 "Summary" 工作表
Public Sub mySummary(w As Workbook, TestInfo As CPLot)

   ' 1. 获取当前产品的参数计算范围定义
   Dim ScopeRng As Range: Set ScopeRng = GetProductScopeDefine(TestInfo.Product)
   If ScopeRng Is Nothing Then
       gShow.PromptInfo "未在 SCOPE_SHEET 中找到产品 " & TestInfo.Product & " 的计算范围定义，将使用全部数据进行统计计算。"
   End If
   
   Dim SummarySheet As Worksheet: Set SummarySheet = w.Worksheets("Summary")
   If SummarySheet Is Nothing Then
       gShow.ErrStop "无法找到 Summary 工作表。"
       Exit Sub
   End If
   
   With SummarySheet
      .Cells.ClearContents ' 清空工作表原有内容
      ' 2. 写入表头
      .Range("a1:c1").Value = Array("Item", "Spec", "Stat")
      
      ' 3. 遍历每个 Wafer
      Dim WaferIndex As Long
      For WaferIndex = 1 To TestInfo.WaferCount
         Application.StatusBar = "参数统计量计算..." & TestInfo.Wafers(WaferIndex).WaferId
         .Cells(1, WaferIndex + 3).Value = TestInfo.Wafers(WaferIndex).WaferId & "#" ' 在第一行写入 Wafer ID
         
         Dim r As Long: r = 2 ' 当前参数写入的起始行号
         Dim i As Long ' 参数索引
         For i = 1 To TestInfo.ParamCount
            ' 4. 仅在处理第一个 Wafer 时，写入参数信息 (Item, Spec, Stat 名称)
            If WaferIndex = 1 Then
               .Cells(r, 1).Value = TestInfo.Params(i).Id & "[" & TestInfo.Params(i).Unit & "]" ' Item 列
               Dim SpecInfo As String: SpecInfo = TestInfo.Params(i).SL & " - " & TestInfo.Params(i).SU
               If IsArray(TestInfo.Params(i).TestCond) Then
                  If UBound(TestInfo.Params(i).TestCond) >= LBound(TestInfo.Params(i).TestCond) Then
                      SpecInfo = SpecInfo & "@" & TestInfo.Params(i).TestCond(LBound(TestInfo.Params(i).TestCond)) ' 添加第一个测试条件
                  End If
               End If
               .Cells(r, 2).Value = SpecInfo ' Spec 列
               ' Stat 列写入统计量名称 (Avg, Std, Median, RobustStd)
               .Cells(r, 3).Value = "Avg."
               .Cells(r + 1, 3).Value = "Std"
               .Cells(r + 2, 3).Value = "Median"
               .Cells(r + 3, 3).Value = "RobustStd"
               ' 复制 Item 和 Spec 信息到下方对应的统计量行
               .Range(.Cells(r, 1), .Cells(r, 2)).Copy .Range(.Cells(r + 1, 1), .Cells(r + 3, 2))
            End If
            
            ' 5. 获取当前 Wafer 当前参数的原始数据
            Dim toFilterData: toFilterData = TestInfo.Wafers(WaferIndex).ChipDatas(i)
            Dim myData ' 用于存储筛选后数据的变量
            
            ' 6. 根据 ScopeRng 筛选数据
            If ScopeRng Is Nothing Then ' 如果未定义范围，则使用全部数据
               myData = toFilterData
            Else
               ' FilterData 函数根据 ScopeRng 中定义的上下限筛选数据
               ' ColIndex 需要对应 ScopeRng 中的列，这里假设 ScopeRng 的列与 Params 对应，且从第3列开始?
               ' 注意：原代码 i + 2 可能需要根据 ScopeRng 的实际结构调整
               myData = FilterData(toFilterData, ScopeRng, i + 2)
            End If
            
            ' 7. 计算统计量并写入单元格
            On Error Resume Next ' 忽略统计函数可能产生的错误 (如 StDev 对少于2个数据点)
            If Not IsArray(myData) Or GetDimension(myData) = 0 Then
               .Cells(r, WaferIndex + 3).Value = "(无有效数据)" ' 筛选后无数据
            ElseIf DimensionLength(myData) < 2 Then ' 数据点太少无法计算 StDev
               .Cells(r, WaferIndex + 3).Value = WorksheetFunction.Average(myData)
               .Cells(r + 1, WaferIndex + 3).Value = "(数据不足)"
               .Cells(r + 2, WaferIndex + 3).Value = WorksheetFunction.Median(myData)
               .Cells(r + 3, WaferIndex + 3).Value = "(数据不足)"
            ElseIf DimensionLength(myData) < 4 Then ' 数据点太少无法计算 Quartile
               .Cells(r, WaferIndex + 3).Value = WorksheetFunction.Average(myData)
               .Cells(r + 1, WaferIndex + 3).Value = WorksheetFunction.StDev_S(myData) ' 使用 StDev_S (样本标准差)
               .Cells(r + 2, WaferIndex + 3).Value = WorksheetFunction.Median(myData)
               .Cells(r + 3, WaferIndex + 3).Value = "(数据不足)"
            Else ' 数据足够计算所有统计量
               .Cells(r, WaferIndex + 3).Value = WorksheetFunction.Average(myData)
               .Cells(r + 1, WaferIndex + 3).Value = WorksheetFunction.StDev_S(myData)
               .Cells(r + 2, WaferIndex + 3).Value = WorksheetFunction.Median(myData)
               ' 计算稳健标准差 (Robust Standard Deviation) = IQR / 1.34898
               .Cells(r + 3, WaferIndex + 3).Value = (WorksheetFunction.Quartile_Inc(myData, 3) _
                                                   - WorksheetFunction.Quartile_Inc(myData, 1)) / 1.34898
            End If
            On Error GoTo 0
            
            r = r + 4 ' 移动到下一个参数的写入行 (每个参数占 4 行)
         Next i
      Next WaferIndex
      
      ' 8. 格式化 Summary 工作表
      .UsedRange.Columns.AutoFit ' 自动调整列宽
      '.UsedRange.AutoFilter ' 可选：添加自动筛选功能
   End With
End Sub

' 根据指定的范围 (ScopeRng) 筛选数据 (toFilterData)
' ColIndex: 指示在 ScopeRng 中查找上下限的列索引 (基于 1)
Private Function FilterData(toFilterData, ScopeRng As Range, ColIndex As Long)
   If GetDimension(toFilterData) = 0 Then Exit Function ' 如果输入数据为空则退出
   
   On Error Resume Next
   Dim ScreenDataLowLimit: ScreenDataLowLimit = ScopeRng.Cells(2, ColIndex).Value ' 获取下限 (第 2 行)
   Dim ScreenDataHighLimit: ScreenDataHighLimit = ScopeRng.Cells(3, ColIndex).Value ' 获取上限 (第 3 行)
   If Err.Number <> 0 Then Exit Function ' 如果读取上下限出错 (例如 ColIndex 超出范围)，则不筛选
   On Error GoTo 0
   
   Dim IsLowLimitValid As Boolean: IsLowLimitValid = IsNumeric(ScreenDataLowLimit)
   Dim IsHighLimitValid As Boolean: IsHighLimitValid = IsNumeric(ScreenDataHighLimit)
   
   ' 如果上下限都无效，则不筛选，返回原始数据
   If Not IsLowLimitValid And Not IsHighLimitValid Then FilterData = toFilterData: Exit Function
   
   Dim ResultList As Object: Set ResultList = CreateObject("System.Collections.ArrayList") ' 使用 ArrayList 动态存储筛选结果
   Dim item As Variant
   For Each item In toFilterData
      If IsNumeric(item) Then ' 只处理数值型数据
         Dim Val As Double: Val = CDbl(item)
         Dim KeepFlag As Boolean: KeepFlag = True
         If IsHighLimitValid Then
             If Val >= ScreenDataHighLimit Then KeepFlag = False
         End If
         If KeepFlag And IsLowLimitValid Then
             If Val <= ScreenDataLowLimit Then KeepFlag = False
         End If
         
         If KeepFlag Then ResultList.Add Val
      End If
   Next
   
   ' 将 ArrayList 转换为 VBA 数组返回
   If ResultList.Count > 0 Then
      FilterData = ResultList.ToArray
   Else
      FilterData = Empty ' 如果没有数据满足条件，返回 Empty
   End If
   
End Function

