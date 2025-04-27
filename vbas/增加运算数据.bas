Attribute VB_Name = "增加运算数据"
Option Explicit

' 定义 Token 类型，用于存储解析后的公式元素
Type Token
   symbol As String  ' 符号（变量名如"f1"或运算符如"+"）
   Flag As Boolean   ' 标记是否为变量 (True) 或运算符/常量 (False)
   VarIndex As Integer ' 如果是变量，存储其在原始参数列表中的索引 (从1开始)
End Type

' 定义解析后的表达式结构
Type ParsExpression
   Count As Integer      ' Token 的数量
   Tokens() As Token   ' 存储解析出的 Token 数组
End Type

' 定义单个计算项的设置
Type CalDataItemSetup
   ItemName As String    ' 新计算项的名称
   Id As String          ' 新计算项的唯一标识 (通常是 "f" + 序号)
   ParamSeq As Integer   ' 新计算项在扩展后参数列表中的最终序号
   CalFormula As String  ' 用户输入的原始计算公式字符串
   Unit As Variant       ' 单位
   SL As Variant         ' 规格下限
   SU As Variant         ' 规格上限
   Expression As ParsExpression ' 解析后的公式结构
End Type

' 定义所有计算项设置的集合
Type CalDataItemSetupInfo
   Count As Integer          ' 计算项的数量
   Rule() As CalDataItemSetup ' 存储所有计算项设置的数组
End Type

' 主函数：向 TestInfo 中添加基于现有参数计算的新数据列
Public Function AddCalData(TestInfo As CPLot)
   Dim mySetupInfo As CalDataItemSetupInfo
   mySetupInfo = ReadSetupInfo() ' 从设置表读取计算规则
   If mySetupInfo.Count = 0 Then Exit Function ' 如果没有定义计算规则，则退出
   
   ' 扩展 TestInfo 结构以容纳新的计算数据
   ExtendDataSize TestInfo, mySetupInfo
   ' 更新 TestInfo 中的参数规格信息 (Params 数组)
   UpdateSpec TestInfo, mySetupInfo
   ' 遍历每个 Wafer，计算并填充新的数据
   UpdateData TestInfo, mySetupInfo
End Function

' 扩展 TestInfo 数据结构的大小以包含新的计算参数
Private Function ExtendDataSize(TestInfo As CPLot, mySetupInfo As CalDataItemSetupInfo)
   Dim OriginalParamCount: OriginalParamCount = TestInfo.ParamCount
   Dim TotalCount: TotalCount = mySetupInfo.Count + OriginalParamCount
   With TestInfo
      .ParamCount = TotalCount
      ReDim Preserve .Params(1 To TotalCount) ' 扩展参数规格数组
      Dim i: For i = 1 To .WaferCount
         .Wafers(i).ParamCount = TotalCount
         ReDim Preserve .Wafers(i).ChipDatas(1 To TotalCount) ' 扩展每个 Wafer 的数据存储数组
         ' 为新参数预分配空间 (空数组)
         Dim NewParamIndex: For NewParamIndex = 1 To mySetupInfo.Count
            Dim x: ReDim x(1 To .Wafers(i).ChipCount, 1 To 1)
            .Wafers(i).ChipDatas(OriginalParamCount + NewParamIndex) = x
         Next
      Next
   End With
End Function

' 更新 TestInfo 中的 Params 数组，添加新计算项的规格信息
Private Function UpdateSpec(TestInfo As CPLot, mySetupInfo As CalDataItemSetupInfo)
   Dim i: For i = 1 To mySetupInfo.Count
      AddNewSpecInfo TestInfo, mySetupInfo.Rule(i)
   Next
End Function

' 遍历所有 Wafer，调用计算函数更新每个 Wafer 的新数据列
Private Function UpdateData(TestInfo As CPLot, mySetupInfo As CalDataItemSetupInfo)
   With mySetupInfo
      Dim i: For i = 1 To .Count
         UpdateWaferData TestInfo, .Rule(i)
      Next
   End With
End Function

' 将单个新计算项的规格信息添加到 TestInfo.Params 数组中
Private Function AddNewSpecInfo(TestInfo As CPLot, myRule As CalDataItemSetup)
   With myRule
      Dim myParamSeq: myParamSeq = .ParamSeq ' 获取新参数的最终序号
   End With
   With TestInfo.Params(myParamSeq)
      .DisplayName = myRule.ItemName
      .Id = myRule.Id  ' 使用设置中的 ItemName 作为 ID 可能更清晰？当前是用 fN
      .SL = myRule.SL
      .SU = myRule.SU
      .Unit = myRule.Unit
      ReDim .TestCond(1 To 1)
      .TestCond(1) = myRule.CalFormula ' 将原始公式存入 TestCond
   End With
End Function

' 更新指定 Wafer 的新计算数据
Private Function UpdateWaferData(TestInfo As CPLot, myRule As CalDataItemSetup)
   With TestInfo
      Dim i: For i = 1 To .WaferCount
         CalNewData .Wafers(i).ChipDatas, myRule
      Next
   End With
End Function

' 核心计算函数：根据解析后的公式 (myRule.Expression) 和现有数据 (ChipDatas)，计算新参数的值
Private Function CalNewData(ChipDatas() As Variant, myRule As CalDataItemSetup)
' 遍历每个 Chip (每一行数据)
Dim Row: For Row = LBound(ChipDatas(1)) To UBound(ChipDatas(1))
   With myRule
      Dim myParamSeq: myParamSeq = .ParamSeq ' 新参数的目标列索引
      Dim CalExpression As String: CalExpression = "" ' 用于构建待 Evaluate 的表达式字符串
      Dim CalFlag As Boolean: CalFlag = True ' 标记当前行的计算是否有效（依赖的数据是否都存在）
      
      ' 遍历解析后的公式 Tokens
      With .Expression
         Dim i: For i = 1 To .Count
            With .Tokens(i)
               If .Flag Then ' 如果是变量 (如 f1)
                  Dim v: v = ChipDatas(.VarIndex)(Row, 1) ' 从 ChipDatas 获取对应变量的值
                  ' 如果依赖的变量值无效 (Error 或 Empty)，则标记计算无效，跳出循环
                  If IsError(v) Then CalFlag = False: Exit For
                  If IsEmpty(v) Then CalFlag = False: Exit For
                  ' 特殊处理，确保 Evaluate 函数能正确处理小于1的小数 (VBA Evaluate 的一个潜在问题)
                  'If v < 1 And v > 0 And v <> 0 Then v = "0" & v
                  CalExpression = CalExpression & CStr(v) ' 将变量值拼接到表达式字符串
               Else ' 如果是运算符或常量
                  CalExpression = CalExpression & .symbol ' 直接将符号拼接到表达式字符串
               End If
            End With
         Next
      End With
      
      ' 如果计算有效 (所有依赖数据都存在)
      If CalFlag Then
         On Error Resume Next ' 暂时忽略 Evaluate 可能产生的错误 (如除零)
         Dim Result: Result = Application.Evaluate(CalExpression) ' 使用 Excel 的 Evaluate 执行计算
         If Err.Number = 0 Then ' 如果 Evaluate 没有出错
             If IsNumeric(Result) Then ' 确保结果是数值类型
                ChipDatas(myParamSeq)(Row, 1) = Result ' 将计算结果存入目标列
             Else
                 ' 可以选择记录错误或置空
                 ChipDatas(myParamSeq)(Row, 1) = CVErr(xlErrNA) ' 标记为 #N/A
             End If
         Else
            ChipDatas(myParamSeq)(Row, 1) = CVErr(xlErrValue) ' Evaluate 出错，标记为 #VALUE!
         End If
         On Error GoTo 0 ' 恢复错误处理
      Else
         ChipDatas(myParamSeq)(Row, 1) = CVErr(xlErrNA) ' 依赖数据缺失，标记为 #N/A
      End If
   End With
Next
End Function

' 从 CAL_DATA_SETUP_SHEET 工作表读取计算项的配置信息
Public Function ReadSetupInfo() As CalDataItemSetupInfo
   Dim Ret As CalDataItemSetupInfo
   On Error Resume Next
   Dim ws As Worksheet: Set ws = CAL_DATA_SETUP_SHEET
   If Err.Number <> 0 Then
       gShow.ErrStop "读取计算数据设置失败", OCAP:="请确保 'Sheet1' (CAL_DATA_SETUP_SHEET) 存在且包含正确的设置。"
       Exit Function
   End If
   On Error GoTo 0
   
   Dim x: x = ws.Range("a1").CurrentRegion.Value
   If Not IsArray(x) Then Exit Function ' 如果读取失败或区域为空
   If UBound(x, 2) < 2 Then Exit Function ' 至少要有名称和ID列
   
   Dim i As Long: For i = 2 To UBound(x, 2)
      ' 检查第三行（计算公式）是否非空，作为有效定义的标志
      If x(3, i) <> "" Then
         With Ret
            .Count = .Count + 1
            ReDim Preserve .Rule(1 To .Count)
            .Rule(.Count) = CreateCalDataItemSetup(x, i)
         End With
      End If
   Next
   ReadSetupInfo = Ret
End Function

' 根据从工作表读取的数组 x 和列索引 i，创建单个 CalDataItemSetup 结构
Private Function CreateCalDataItemSetup(x, i) As CalDataItemSetup
   Dim Ret As CalDataItemSetup
   With Ret
      .ItemName = x(1, i) ' 第一行：项目名称
      .Id = x(2, i)       ' 第二行：项目ID (格式应为 fN)
      .ParamSeq = SplitVarIndex(.Id) ' 从 ID (fN) 提取序号 N 作为参数序号
      .CalFormula = x(3, i) ' 第三行：计算公式
      .Expression = ParseFormula(.CalFormula) ' 解析公式字符串为 Token 结构
      .Unit = x(4, i)     ' 第四行：单位
      .SL = x(5, i)       ' 第五行：规格下限
      .SU = x(6, i)       ' 第六行：规格上限
   End With
   CreateCalDataItemSetup = Ret
End Function

' 解析公式字符串 (myFormula)，将其分解为 Token 数组，存储在 ParsExpression 结构中
' 假设变量格式为 fN (N为数字)
Private Function ParseFormula(myFormula As String) As ParsExpression
   Dim Ret As ParsExpression
   Dim Start As Long: Start = 1
   Dim State As String ' 状态机状态: "" (初始/运算符), "Var" (变量)
   Dim Group As String ' 当前字符组类型: "f", "d" (数字), "else" (其他)
   Dim Index As Long
   
   For Index = 1 To Len(myFormula)
      Dim s As String: s = Mid(myFormula, Index, 1)
      Select Case LCase(s) ' 忽略大小写
      Case "f"
         If State <> "Var" Then ' 如果之前不是变量状态
            ' 将 f 之前的非变量部分（运算符/常量）添加为 Token
            If Start < Index Then AddToken Ret, CreateToken(myFormula, Start, Index - 1, False)
            State = "Var" ' 进入变量状态
            Start = Index ' 记录变量开始位置
         Else ' 如果之前已经是变量状态 (理论上不应出现 ff)
             ' 可能是公式错误，这里简单处理：结束之前的变量，开始新的 f
            AddToken Ret, CreateToken(myFormula, Start, Index - 1, True) ' 结束旧变量
            Start = Index ' 开始新变量（可能是错误的）
            State = "Var"
         End If
         Group = "f"
      Case "0" To "9"
         If State = "Var" Then
             Group = "d" ' 在变量状态下遇到数字，标记为数字组
         Else ' 不在变量状态下遇到数字
             If Group <> "d" And Start < Index Then ' 如果前面不是数字，且有内容，则把前面的内容加为Token
                 AddToken Ret, CreateToken(myFormula, Start, Index - 1, False)
                 Start = Index
             End If
             Group = "d" ' 标记为数字组（作为常量的一部分）
         End If
      Case Else ' 其他字符 (运算符, 括号等)
         If State = "Var" Then ' 如果之前是变量状态
            ' 变量结束，将变量 (fN) 添加为 Token
            AddToken Ret, CreateToken(myFormula, Start, Index - 1, True)
            State = "" ' 退出变量状态
            Start = Index ' 记录当前运算符/括号的开始位置
         Else ' 如果之前不是变量状态
             If Start < Index Then ' 将之前的运算符/常量添加为 Token
                AddToken Ret, CreateToken(myFormula, Start, Index - 1, False)
             End If
             Start = Index ' 记录当前运算符/括号的开始位置
         End If
         Group = "else"
      End Select
   Next
   
   ' 处理公式末尾剩余的部分
   AddToken Ret, CreateToken(myFormula, Start, Len(myFormula), State = "Var")
   
   ParseFormula = Ret
End Function

' 将新创建的 Token 添加到 ParsExpression 结构的 Tokens 数组中
Private Function AddToken(Ret As ParsExpression, newToken As Token)
   With Ret
      .Count = .Count + 1
      ReDim Preserve .Tokens(1 To .Count)
      .Tokens(.Count) = newToken
   End With
End Function

' 根据公式片段创建 Token 结构
Private Function CreateToken(myFormula As String, Start, Finish, VarFlag As Boolean) As Token
   Dim Ret As Token
   With Ret
      .Flag = VarFlag ' 标记是否为变量
      .symbol = Mid(myFormula, Start, Finish - Start + 1) ' 提取符号字符串
      If .Flag Then ' 如果是变量 (fN)
         .VarIndex = SplitVarIndex(.symbol) ' 从符号中提取参数索引 N
      End If
   End With
   CreateToken = Ret
End Function

' 从变量符号 (如 "f12") 中提取参数索引 (12)
Private Function SplitVarIndex(symbol) As Integer
   On Error Resume Next ' 防止 Val 对非数字部分报错
   SplitVarIndex = Val(Mid(symbol, 2)) ' 从第二个字符开始取值
   On Error GoTo 0
End Function

' 检查增加计算数据的设置是否正确
Public Function SetupCheck_ADD_CAL_DATA(TestInfo As CPLot) As Boolean
   Dim SetupOk As Boolean: SetupOk = True ' 默认设置为 True
   Dim r As CalDataItemSetupInfo: r = ReadSetupInfo()
   If r.Count = 0 Then SetupCheck_ADD_CAL_DATA = True: Exit Function ' 没有设置则认为OK
   
   Dim OriginalParamCount As Integer: OriginalParamCount = TestInfo.ParamCount
   
   With r
      Dim i: For i = 1 To .Count
         ' 检查规则 ID (fN) 中的序号 N 是否等于 原始参数数量 + 当前规则序号 i
         If .Rule(i).ParamSeq <> OriginalParamCount + i Then
            gShow.ErrAlarm Array("运算项目定义的第" & i & "项:", _
                                 .Rule(i).Id, _
                                 "命名或顺序不正确", _
                                 "预期ID应为 f" & OriginalParamCount + i)
            SetupOk = False ' 标记设置错误
         End If
         
         ' 检查公式中使用的变量是否有效
         With .Rule(i).Expression
            Dim j: For j = 1 To .Count
               If .Tokens(j).Flag Then ' 只检查变量 Token
                  Dim VarIdx As Integer: VarIdx = .Tokens(j).VarIndex
                  ' 如果变量索引大于原始参数数量
                  If VarIdx > OriginalParamCount Then
                      ' 检查这个变量是否是本次计算中前面已定义的某个新变量
                     If IsNewVarNameExists(.Tokens(j).symbol, r, i) = False Then
                        gShow.ErrAlarm Array("运算项目定义中计算表达式存在错误:", _
                                             "公式: " & r.Rule(i).CalFormula, _
                                             "项目: " & r.Rule(i).Id,
                                             "使用了未定义的变量: " & .Tokens(j).symbol)
                        SetupOk = False ' 标记设置错误
                     End If
                  End If
               End If
            Next
         End With
      Next
   End With
   SetupCheck_ADD_CAL_DATA = SetupOk
End Function

' 检查一个变量名 (toCheckName, 如 fN) 是否是在当前计算项 (CurItemIndex) 之前定义的某个新计算项的 ID
Private Function IsNewVarNameExists(toCheckName, r As CalDataItemSetupInfo, CurItemIndex) As Boolean
   Dim Ret As Boolean: Ret = False
   With r
       ' 只检查当前项之前的规则
      Dim i: For i = 1 To CurItemIndex - 1
         If LCase(.Rule(i).Id) = LCase(toCheckName) Then ' 比较 ID (忽略大小写)
            Ret = True: Exit For
         End If
      Next
   End With
   IsNewVarNameExists = Ret
End Function
