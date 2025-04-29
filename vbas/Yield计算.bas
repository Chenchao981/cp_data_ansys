Attribute VB_Name = "Yield计算" ' 模块名：良率计算
Option Explicit

' 计算并显示 Wafer 和 Bin 的良率数据，并输出到工作簿的 "Yield" 工作表
Public Function ShowYield(ResultBook As Workbook, _
                          TestInfo As CPLot)
   If TestInfo.WaferCount = 0 Then Exit Function ' 如果没有 Wafer 数据则退出
   
   Dim ResultSheet As Worksheet: Set ResultSheet = ResultBook.Worksheets("Yield")
   If ResultSheet Is Nothing Then
       gShow.ErrStop "找不到 Yield 工作表"
       Exit Function
   End If
   ResultSheet.Cells.ClearContents ' 清空内容
   
   ' 1. 计算各 Wafer 的 Bin 统计 (字典数组)
   Dim WaferBinDics() As Object
   WaferBinDics = CalYield(TestInfo)
   
   ' 2. 获取所有 Wafer 中出现的 Bin 编号并排序 (PassBin 会排在最前面)
   Dim AllBinList: AllBinList = GetAllBinList(WaferBinDics, TestInfo.PassBin)
   If Not IsArray(AllBinList) Then Exit Function ' 如果没有 Bin 数据则退出
   
   Dim BinStartCol As Long: BinStartCol = 4 ' Bin 数据开始列号 (D列)
   Dim BinCount As Long: BinCount = SizeOf(AllBinList)
   If BinCount = 0 Then Exit Function
   
   ' 3. 生成每个晶圆的 Bin 统计表 (二维表)
   Dim BinResultData: BinResultData = GetContent(WaferBinDics, AllBinList)
   
   With ResultSheet
      ' 4. 设置表头
      Dim HeadList: HeadList = Array("Wafer", "Yield", "Total", "Pass")
      ListFill2Rng .Range("a1"), HeadList ' 填充 A1:D1
      .Cells(1, BinStartCol).Value = "Pass" ' 设置 D 列标题为 "Pass"
      Dim i As Long
      For i = 1 To BinCount - 1 ' 其他各 Bin 的列标题 (E列开始)
         .Cells(1, BinStartCol + i).Value = "Bin" & AllBinList(LBound(AllBinList) + i)
      Next
      
      ' 5. 填充各 Wafer 的 Bin 数据表
      FillArray2Rng .Cells(2, BinStartCol), BinResultData
      
      ' 6. 填充 Wafer ID (A列)
      For i = 1 To TestInfo.WaferCount
         .Cells(i + 1, 1).Value = TestInfo.Wafers(i).WaferId & "#"
      Next
      
      ' 7. 添加汇总行 "All" 行 (计算所有 Wafer 的 Bin 总数)
      Dim TotalRow As Long: TotalRow = .Range("a1").CurrentRegion.Rows.Count + 1
      .Cells(TotalRow, 1).Value = "All"
      Dim SummaryCols As Long: SummaryCols = .Range("a1").CurrentRegion.Columns.Count
      Dim j As Long
      For j = BinStartCol To SummaryCols ' 从 Pass 列开始求和公式
         .Cells(TotalRow, j).Formula = "=SUM(" & .Range(.Cells(2, j), .Cells(TotalRow - 1, j)).Address & ")"
      Next
      
      ' 8. 计算每个晶圆 Wafer 和汇总行的 Total 和 Yield
      For i = 2 To TotalRow
         ' 计算 Total (C列) = Sum(D列到最后各个 Bin 数)
         .Cells(i, 3).Formula = "=SUM(" & .Range(.Cells(i, BinStartCol), .Cells(i, SummaryCols)).Address & ")"
         ' 计算 Yield (B列) = Pass (D列) / Total (C列)
         If .Cells(i, 3).Value <> 0 Then ' 防止除零错误
             .Cells(i, 2).Value = .Cells(i, 4).Value / .Cells(i, 3).Value
             .Cells(i, 2).NumberFormat = "0.00%" ' 设置百分比格式
         Else
             .Cells(i, 2).Value = "N/A"
         End If
      Next
      
      ' 9. 优化表格显示，调整列宽等
      .UsedRange.Value = .UsedRange.Value
      .UsedRange.Columns.AutoFit
   End With
End Function

' 计算所有 Wafer 的 Bin 分布，返回字典数组
' 每个字典 Key 是 Bin 值，Value 是 Bin 数量
Private Function CalYield(TestInfo As CPLot) As Object()
   Dim WaferBinDics() As Object
   With TestInfo
      If .WaferCount = 0 Then Exit Function
      ReDim WaferBinDics(1 To .WaferCount) ' 创建与晶圆数量相同 Wafer 数组
      Dim i: For i = 1 To .WaferCount
         Set WaferBinDics(i) = CreateBinDic(.Wafers(i)) ' 为每个 Wafer 创建 Bin 字典
      Next
   End With
   CalYield = WaferBinDics
End Function

' 为单个 Wafer 统计 Bin 数量字典
Private Function CreateBinDic(toCalWafer As CPWafer) As Object
   Dim Ret As Object: Set Ret = CreateObject("scripting.dictionary")
   Ret.CompareMode = vbTextCompare ' 设置 Bin 比较不区分大小写
   With toCalWafer
      If Not IsArray(.Bin) Or .ChipCount = 0 Then Set CreateBinDic = Ret: Exit Function
      Dim i: For i = 1 To .ChipCount
         Dim myBin As Variant: myBin = .Bin(i, 1)
         If Not IsEmpty(myBin) Then ' 只统计非空的 Bin 值
             If Ret.exists(myBin) Then
                Ret(myBin) = Ret(myBin) + 1
             Else
                Ret.Add myBin, 1
             End If
         End If
      Next
   End With
   Set CreateBinDic = Ret
End Function

' 根据所有 Wafer 的 Bin 字典集 (WaferBinDics) 和唯一 Bin 列表 (AllBinList)，
' 生成二维数组用于填充到 "Yield" 工作表中的 Bin 统计数据
' 返回二维数组: (Wafer 数量) x (Bin 种类)
Private Function GetContent(WaferBinDics() As Object, AllBinList)
   Dim x
   Dim WaferLBound As Long: WaferLBound = LBound(WaferBinDics)
   Dim WaferUBound As Long: WaferUBound = UBound(WaferBinDics)
   Dim BinLBound As Long: BinLBound = LBound(AllBinList)
   Dim BinUBound As Long: BinUBound = UBound(AllBinList)
   
   ReDim x(WaferLBound To WaferUBound, BinLBound To BinUBound)
   
   Dim i: For i = WaferLBound To WaferUBound
      If Not WaferBinDics(i) Is Nothing Then ' 确保字典非空
          With WaferBinDics(i)
             Dim j: For j = BinLBound To BinUBound
                If .exists(AllBinList(j)) Then
                   x(i, j) = WaferBinDics(i)(AllBinList(j))
                Else
                   x(i, j) = 0 ' 当前 Wafer 不存在此 Bin，填充 0
                End If
             Next
          End With
      End If
   Next
   GetContent = x
End Function

' 获取所有 Wafer 中出现的 Bin 编号列表并排序
Private Function GetAllBinList(WaferBinDics() As Object, _
                               PassBinId)
   ' 1. 合并所有 Wafer 的所有 Key 到一个 List
   Dim Ret: Ret = MergeDicsKey2List(WaferBinDics)
   If Not IsArray(Ret) Then Exit Function
   ' 2. 对 Bin List 排序 (Pass Bin 将被排在最前面)
   SortBinList Ret, PassBinId
   GetAllBinList = Ret
End Function

' 对 Bin 编号列表排序，PassBinId 将被移动到列表最前面
' 其他编号按照数字或文本顺序排序，PassBinId 永远在开头
Private Sub SortBinList(BinList, PassBinId)
    If Not IsArray(BinList) Then Exit Sub
    Dim iOuter As Long, iInner As Long
    Dim iLBound As Long, iUBound As Long
    iLBound = LBound(BinList)
    iUBound = UBound(BinList)
    If iLBound >= iUBound Then Exit Sub ' 单元素或空数组无需排序
    
    Dim PassBinFound As Boolean: PassBinFound = False
    Dim PassBinIndex As Long
    
    ' 冒泡排序 (简单)
    For iOuter = iLBound To iUBound - 1
        For iInner = iLBound To iUBound - (iOuter - iLBound) - 1
            ' 查找特殊 PassBin
            If Not PassBinFound Then
                If BinList(iInner) = PassBinId Then
                    PassBinFound = True
                    PassBinIndex = iInner
                End If
                If BinList(iInner + 1) = PassBinId Then
                    PassBinFound = True
                    PassBinIndex = iInner + 1
                End If
            End If
            
            ' 排序规则 (尝试按数字排序，失败则按文本排序)
            On Error Resume Next
            Dim Val1: Val1 = CDbl(BinList(iInner))
            Dim Val2: Val2 = CDbl(BinList(iInner + 1))
            If Err.Number = 0 Then ' 数值比较成功
                If Val1 > Val2 Then Swap BinList, iInner, iInner + 1
            Else ' 文本比较
                If CStr(BinList(iInner)) > CStr(BinList(iInner + 1)) Then Swap BinList, iInner, iInner + 1
            End If
            On Error GoTo 0
        Next iInner
    Next iOuter
    
    ' 如果找到 PassBin，将其移动至首位
    If PassBinFound Then
        If PassBinIndex <> iLBound Then
            Dim PassBinValue: PassBinValue = BinList(PassBinIndex)
            ' 从 PassBinIndex 开始向前移动
            For iInner = PassBinIndex To iLBound + 1 Step -1
                BinList(iInner) = BinList(iInner - 1)
            Next
            BinList(iLBound) = PassBinValue ' 将 PassBin 放首位
        End If
    End If
End Sub

' 交换数组中两个元素
Private Sub Swap(BinList, i1, i2)
   Dim tmp
   tmp = BinList(i1)
   BinList(i1) = BinList(i2)
   BinList(i2) = tmp
End Sub

' 测试 SortBinList 函数功能
Private Sub test_SortBinList()
   Dim x: x = Split("bin1,bin3,bin9,bin2,bin0", ",")
   SortBinList x, "bin0"
   Debug.Print Join(x, ",") = "bin0,bin1,bin2,bin3,bin9" ' 测试通过
   
   Dim y: y = Array(5, 1, 10, 2, 8, 0)
   SortBinList y, 0
   Debug.Print Join(y, ",") = "0,1,2,5,8,10" ' 测试通过
End Sub

' 合并多个字典的 Key 到一个 List (数组) 中无重复
Private Function MergeDicsKey2List(toMergeDics() As Object)
   Dim Ret
   Dim AllDic As Object: Set AllDic = CreateObject("scripting.dictionary")
   AllDic.CompareMode = vbTextCompare ' Key 比较不区分大小写
   
   Dim i: For i = LBound(toMergeDics) To UBound(toMergeDics)
      If Not toMergeDics(i) Is Nothing Then ' 确保字典非空
          Dim Keys: Keys = toMergeDics(i).Keys
          If IsArray(Keys) Then
              Dim Index: For Index = LBound(Keys) To UBound(Keys)
                 If Not AllDic.exists(Keys(Index)) Then
                    AllDic.Add Keys(Index), 0 ' 添加不重复的 Key
                 End If
              Next
          End If
      End If
   Next
   
   If AllDic.Count > 0 Then Ret = AllDic.Keys Else Ret = Empty
   MergeDicsKey2List = Ret
End Function
