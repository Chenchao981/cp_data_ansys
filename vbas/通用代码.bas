Attribute VB_Name = "通用代码"
Option Explicit

' 以 Tab 分隔符方式打开文本文件
Public Function OpenTabTextxlDelimitedFile(fName) As Workbook
   On Error Resume Next ' 忽略可能的打开错误
   Workbooks.OpenText Filename:=fName, _
      Origin:=1251, StartRow:=1, DataType:=xlDelimited, Tab:=True, _
      FieldInfo:=Array(Array(1, 1), Array(2, 1)), TrailingMinusNumbers:=True ' Origin 1251 对应 Windows ANSI (Cyrillic)
   If Err.Number <> 0 Then
       gShow.ErrAlarm "打开文件失败: " & fName & vbCrLf & Err.Description
       Set OpenTabTextxlDelimitedFile = Nothing
   Else
       Set OpenTabTextxlDelimitedFile = ActiveWorkbook
   End If
   On Error GoTo 0
End Function

' 弹出文件选择对话框，让用户选择文件
' FileDescription: 对话框中显示的文件类型描述
' MultiSelect: 是否允许多选
' ExtendName: 可变参数数组，包含允许的文件扩展名 (不带点，如 "txt", "csv")
Public Function PickupFile(FileDescription, MultiSelect As Boolean, ParamArray ExtendName())
   Dim Ret
   Dim f As String, p: p = ExtendName
   f = CreateFileFilter(p) ' 创建文件过滤器字符串
   Dim tmpFiles
   tmpFiles = Application.GetOpenFilename(FileFilter:=FileDescription & " (" & f & ")," & f, _
                                    Title:="选择" & FileDescription, MultiSelect:=MultiSelect)
   
   ' 检查用户是否取消了选择
   If VarType(tmpFiles) = vbBoolean Then Exit Function
   
   If MultiSelect Then
      ' 如果允许多选，GetOpenFilename 返回一个包含文件路径的数组
      QuickSort tmpFiles ' 对选择的文件列表进行排序 (按文件名)
      Ret = tmpFiles
   Else
      ' 如果只允许单选，GetOpenFilename 返回一个字符串
      ' 将其包装成单元素数组，以保持返回类型一致
      ReDim Ret(1 To 1)
      Ret(1) = tmpFiles
   End If
   PickupFile = Ret
End Function

' 根据扩展名列表创建 GetOpenFilename 需要的文件过滤器字符串
' 例如，输入 ("xls", "xlsx") 返回 "*.xls;*.xlsx"
Private Function CreateFileFilter(ExtendNameList) As String
   Dim Ret As String
   Dim x: x = ExtendNameList
   Dim i: For i = LBound(ExtendNameList) To UBound(ExtendNameList)
      x(i) = "*." & x(i) ' 为每个扩展名添加 "*."
   Next
   Ret = Join(x, ";") ' 用分号连接
   CreateFileFilter = Ret
End Function

' 对数组进行快速排序 (升序)
Public Sub QuickSort(ByRef x)
    Dim iLBound As Long
    Dim iUBound As Long
    Dim iTemp
    Dim iOuter As Long
    Dim iMax As Long
  
    iLBound = LBound(x)
    iUBound = UBound(x)
  
    ' 如果数组只有一个元素或为空，则无需排序
    If (iUBound <= iLBound) Then Exit Sub
    
    ' 将最大值移到末尾 (这个步骤似乎不是标准快速排序的一部分，可能是某种优化或特定需求?)
    ' 标准快速排序通常选择第一个、最后一个或中间元素作为基准
    iMax = iLBound
    For iOuter = iLBound + 1 To iUBound
        If x(iOuter) > x(iMax) Then iMax = iOuter
    Next iOuter
    iTemp = x(iMax)
    x(iMax) = x(iUBound)
    x(iUBound) = iTemp
  
    ' 开始标准的快速排序递归过程
    InnerQuickSort x, iLBound, iUBound - 1 ' 对除了最后一个(最大值)之外的部分进行排序
End Sub

' 快速排序的内部递归函数
Private Sub InnerQuickSort(ByRef x, ByVal iLeftEnd As Long, ByVal iRightEnd As Long)
    Dim iLeftCur As Long
    Dim iRightCur As Long
    Dim iPivot
    Dim iTemp
  
    ' 递归终止条件
    If iLeftEnd >= iRightEnd Then Exit Sub
  
    ' 选择第一个元素作为基准 (Pivot)
    iLeftCur = iLeftEnd
    iRightCur = iRightEnd + 1
    iPivot = x(iLeftEnd)
  
    Do
        ' 从左向右查找第一个大于等于基准的元素
        Do
            iLeftCur = iLeftCur + 1
            If iLeftCur > iRightEnd Then Exit Do ' 防止越界
        Loop While x(iLeftCur) < iPivot
       
        ' 从右向左查找第一个小于等于基准的元素
        Do
            iRightCur = iRightCur - 1
            If iRightCur < iLeftEnd Then Exit Do ' 防止越界
        Loop While x(iRightCur) > iPivot
       
        ' 如果左右指针交叉，则本轮分区结束
        If iLeftCur >= iRightCur Then Exit Do
       
        ' 交换左右指针指向的元素
        iTemp = x(iLeftCur)
        x(iLeftCur) = x(iRightCur)
        x(iRightCur) = iTemp
    Loop
  
    ' 将基准元素放到正确的位置 (iRightCur 指向的位置)
    x(iLeftEnd) = x(iRightCur)
    x(iRightCur) = iPivot
  
    ' 对基准左右两边的子数组进行递归排序
    InnerQuickSort x, iLeftEnd, iRightCur - 1
    InnerQuickSort x, iRightCur + 1, iRightEnd
End Sub

' 确保名称唯一性。如果 toCheckName 在 NameDic 中已存在，则在末尾添加数字后缀 (2, 3, ...) 直到唯一
' NameDic: 一个 Scripting.Dictionary 对象，用于存储已使用的名称
Public Function Change2UniqueName(toCheckName As String, NameDic As Object) As String
   Dim Ret As String: Ret = toCheckName
   ' 如果 NameDic 未初始化，则创建新的字典对象
   If NameDic Is Nothing Then Set NameDic = CreateObject("scripting.dictionary")
   Dim k As Integer: k = 1
   Do While NameDic.exists(Ret)
      k = k + 1
      Ret = toCheckName & k
   Loop
   NameDic.Add Ret, 1 ' 将新生成的唯一名称添加到字典中
   Change2UniqueName = Ret
End Function

' 从字符串中提取由一对特定字符包围的内容
' 例如: SplitContentInPairChar("abc[xyz]def", "[]") 返回 "xyz"
Public Function SplitContentInPairChar(toSplitInfo, Optional PairChar = "[]") As String
   If Len(PairChar) < 2 Then Exit Function ' 必须提供一对字符
   Dim Ret As String
   Dim LeftChar As String: LeftChar = Left(PairChar, 1)
   Dim RightChar As String: RightChar = Right(PairChar, 1) ' 修正：应取最后一个字符
   
   Dim PosLeft As Long: PosLeft = InStr(1, toSplitInfo, LeftChar)
   Dim PosRight As Long: PosRight = InStrRev(toSplitInfo, RightChar)
   
   If PosLeft > 0 And PosRight > PosLeft Then
       Ret = Mid(toSplitInfo, PosLeft + 1, PosRight - PosLeft - 1)
   End If

   SplitContentInPairChar = Ret
End Function

' 创建一个新的 Excel 工作簿，并根据提供的名称列表 (SheetNames) 创建工作表
' SheetNames: 可以是数组或逗号分隔的字符串
Public Function CreateResultBook(Optional SheetNames) As Workbook
   Dim SheetNameList: SheetNameList = CheckList(SheetNames) ' 处理输入参数，确保是数组
   Dim ww As Workbook
   Dim AdjustNewSheetNumFlag As Boolean: AdjustNewSheetNumFlag = IsArray(SheetNameList)
   Dim OldSheetNum As Integer
   
   On Error Resume Next ' 忽略可能的错误
   If AdjustNewSheetNumFlag And IsArrayNotEmpty(SheetNameList) Then
      Dim NewSheetNum As Integer: NewSheetNum = UBound(SheetNameList) - LBound(SheetNameList) + 1
      If NewSheetNum > 0 Then
          OldSheetNum = Application.SheetsInNewWorkbook
          Application.SheetsInNewWorkbook = NewSheetNum ' 临时设置新建工作簿时的默认工作表数量
      Else
          AdjustNewSheetNumFlag = False ' 如果名称列表为空，则按默认设置创建
      End If
   End If
   
   Set ww = Workbooks.Add ' 创建新工作簿
   
   If AdjustNewSheetNumFlag Then
      Application.SheetsInNewWorkbook = OldSheetNum ' 恢复默认设置
      If Not ww Is Nothing Then ' 确保工作簿已成功创建
         With ww
            Dim Index As Integer: Index = LBound(SheetNameList)
            Dim j As Integer: For j = 1 To .Worksheets.Count
               If Index <= UBound(SheetNameList) Then
                   .Worksheets(j).Name = SheetNameList(Index)
                   Index = Index + 1
               Else
                   ' 如果提供的名称少于实际创建的工作表，则可以删除多余的或保留默认名称
                   ' Application.DisplayAlerts = False
                   ' .Worksheets(j).Delete
                   ' Application.DisplayAlerts = True
               End If
            Next
         End With
      End If
   End If
   On Error GoTo 0 ' 恢复错误处理
   
   Set CreateResultBook = ww
End Function

' 从工作表中获取指定列、指定起始行和行数的数据范围 (Range 对象)
Public Function GetList(WaferDataSheet As Worksheet, _
                         SpecificCol As Integer, _
                         StartRow As Long, DataCount As Long) As Range
   Dim Ret As Range
   If DataCount <= 0 Then Exit Function ' 如果行数为 0 或负数，返回 Nothing
   On Error Resume Next
   Set Ret = WaferDataSheet.Cells(StartRow, SpecificCol).Resize(DataCount)
   If Err.Number <> 0 Then Set Ret = Nothing ' 获取范围出错则返回 Nothing
   On Error GoTo 0
   Set GetList = Ret
End Function

' 根据单位前缀 (n, u, m, k) 获取数量级转换率 (相对于标准单位)
Public Function GetUnitOrderChangeRate(Unit As String) As Double
   Dim Ret As Double: Ret = 1 ' 默认为 1
   If Len(Unit) = 0 Then GetUnitOrderChangeRate = 1: Exit Function
   
   Select Case LCase(Left(Unit, 1))
      Case "n": Ret = 1E-09
      Case "u": Ret = 1E-06
      Case "m": Ret = 0.001
      Case "k": Ret = 1000
      Case Else: Ret = 1
   End Select
   GetUnitOrderChangeRate = Ret
End Function

' 计算从旧单位 (oldUnit) 转换到新单位 (newUnit) 的比率
Public Function GetUnitChangeRate(newUnit, oldUnit) As Double
   Dim Ret As Double
   Dim newRate As Double: newRate = GetUnitOrderChangeRate(newUnit)
   Dim oldRate As Double: oldRate = GetUnitOrderChangeRate(oldUnit)
   If oldRate = 0 Then GetUnitChangeRate = 0: Exit Function ' 避免除零错误
   Ret = newRate / oldRate
   GetUnitChangeRate = Ret
End Function

' 将一个以标准单位表示的值，根据目标单位 (Unit) 进行转换
Public Function ChangeWithUnit(ValueWithStdUnit, Unit As String) As Variant
   Dim Ret As Variant
   If IsEmpty(ValueWithStdUnit) Or Not IsNumeric(ValueWithStdUnit) Then
       ChangeWithUnit = ValueWithStdUnit ' 如果输入无效，则原样返回
       Exit Function
   End If
   Dim Rate As Double: Rate = 1 / GetUnitOrderChangeRate(Unit) ' 计算从标准单位到目标单位的乘数
   Ret = CDbl(ValueWithStdUnit) * Rate
   ChangeWithUnit = Ret
End Function

' 使用选择性粘贴将 UnitRateRng 的值乘以 DataRng 区域的值
' 通常用于将数据区域的值从某个单位批量转换为标准单位或另一单位
Public Sub ChangeRangeUnit(UnitRateRng As Range, DataRng As Range)
    On Error Resume Next
    UnitRateRng.Copy
    DataRng.PasteSpecial Paste:=xlPasteValues, Operation:=xlMultiply, SkipBlanks:=True
    Application.CutCopyMode = False ' 清除剪贴板
    If Err.Number <> 0 Then
        gShow.ErrAlarm "范围单位转换失败: " & Err.Description
    End If
    On Error GoTo 0
End Sub


' 将传入的变量 (info) 转换为字符串，如果是数组则用换行符连接各元素
Function Info2Str(info) As String
   Dim Ret As String
   If IsArray(info) Then
      Dim x() As String: ReDim x(LBound(info) To UBound(info))
      Dim i: For i = LBound(info) To UBound(info)
         x(i) = Info2Str(info(i)) ' 递归调用处理数组元素
      Next
      Ret = Join(x, vbCrLf)
   Else
      Ret = CStr(info) ' 强制转换为字符串
   End If
   Info2Str = Ret
End Function
