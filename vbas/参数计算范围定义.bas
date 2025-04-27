Attribute VB_Name = "参数计算范围定义"
Option Explicit

' 根据产品名称 (ProductName) 从 SCOPE_SHEET 工作表中查找并返回对应的参数计算范围定义区域
' SCOPE_SHEET 结构预期：
'   - A 列从第 2 行开始是产品名称列表
'   - 每个产品名称对应一行，该行及下方两行 (共三行) 定义了该产品下各个参数的计算范围
'   - 第一行通常是参数名称或其他标识
'   - 第二行 (与产品名称同行的下一行) 是计算范围下限
'   - 第三行 (产品名称行的下两行) 是计算范围上限
' 返回值: 一个包含参数标识行、下限行和上限行共 3 行数据的 Range 对象。如果找不到产品名称，则返回 Nothing
Public Function GetProductScopeDefine(ProductName) As Range
   If Len(ProductName) = 0 Then Exit Function ' 产品名称为空则退出
   
   Dim ProductRow As Long: ProductRow = 0 ' 初始化找到的产品所在行号
   Dim ScopeWs As Worksheet: Set ScopeWs = SCOPE_SHEET
   If ScopeWs Is Nothing Then
       gShow.ErrAlarm "无法访问参数计算范围定义工作表 (SCOPE_SHEET)。"
       Exit Function
   End If
   
   On Error Resume Next
   Dim x: x = ScopeWs.Range("a1").CurrentRegion.Value ' 读取整个范围定义表到数组
   If Err.Number <> 0 Or Not IsArray(x) Then
       gShow.ErrAlarm "读取参数计算范围定义表内容失败。"
       Exit Function
   End If
   On Error GoTo 0
   
   ' 从第二行开始查找产品名称 (忽略大小写和前后空格)
   Dim i: For i = 2 To UBound(x, 1)
      If LCase(Trim(x(i, 1))) = LCase(Trim(ProductName)) Then
         ProductRow = i
         Exit For
      End If
   Next
   
   ' 如果找到了产品名称 (ProductRow > 0)
   If ProductRow > 0 Then
       ' 返回包含参数标识行、下限行、上限行的 Range 对象
       ' 返回的区域是从 产品名称行的上一行 (ProductRow - 1) 开始，共 3 行，列数与读取的区域一致
       Set GetProductScopeDefine = ScopeWs.Cells(ProductRow - 1, 1).Resize(3, UBound(x, 2))
   Else
       ' 如果没找到，返回 Nothing (调用方需要处理此情况)
       Set GetProductScopeDefine = Nothing
   End If
   
End Function
