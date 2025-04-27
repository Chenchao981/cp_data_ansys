Attribute VB_Name = "通用数组操作函数"
Option Explicit

' 本模块提供通用的数组（在此称为 List, Vector, Table）操作函数
' 定义: 一维数组为 List, 只有1列的二维数组为 Vector, 多维数组为 Table

' 引入 Windows API 函数用于获取数组维度 (注意: 对 Variant 类型的动态数组可能无效)
Private Declare Function SafeArrayGetDim Lib "oleaut32.dll" (ByRef saArray() As Any) As Long

'========== 数组状态识别函数 ================

' 判断数组是否为空 (未初始化或 ReDim 后未赋值)
' 使用 GetDimension 函数通过错误处理来判断
Function IsArrayEmpty(toCheckArray) As Boolean
   IsArrayEmpty = (GetDimension(toCheckArray) = 0)
End Function

' 判断数组是否非空 (已初始化且至少有一个维度)
Function IsArrayNotEmpty(toCheckArray) As Boolean
   IsArrayNotEmpty = (GetDimension(toCheckArray) > 0)
End Function

' 获取数组的维度数量
' 通过尝试访问不同维度的 UBound 来确定，最多检查 60 维
' 对 Variant 类型数组有效
Function GetDimension(toCheckArray)
   Dim Result
   Dim i As Long
   On Error Resume Next
   For i = 1 To 60 ' VBA 数组最多支持 60 维
      Result = UBound(toCheckArray, i)
      If Err.Number <> 0 Then Exit For ' 如果访问 UBound 出错，说明维度不存在
   Next
   On Error GoTo 0
   GetDimension = i - 1 ' 实际维度是最后一个成功访问的索引
End Function

' 获取数组指定维度的长度 (元素个数)
Public Function DimensionLength(toCheckArray, Optional Dimension = 1)
   If GetDimension(toCheckArray) >= Dimension Then
      On Error Resume Next
      DimensionLength = UBound(toCheckArray, Dimension) - LBound(toCheckArray, Dimension) + 1
      If Err.Number <> 0 Then DimensionLength = 0 ' 处理 LBound > UBound 的空数组情况
      On Error GoTo 0
   Else
      DimensionLength = 0 ' 维度不存在
   End If
End Function

' 安全地复制数组或对象的值
' 如果源是对象，则使用 Set；否则直接赋值
Sub ArrayValueCopy(Target, Source)
   If IsObject(Source) Then
      Set Target = Source
   Else
      Target = Source
   End If
End Sub

'=========== 扩展操作函数 ===============

' 扩展一个 List (一维数组) 的大小，增加指定数量的空元素
Function ExpandBlank2List(toExpandList, Optional ExpandCount = 1)
   Dim Result
   Result = toExpandList
   If ExpandCount > 0 Then
      If GetDimension(Result) = 0 Then ' 如果原数组为空
         ReDim Result(1 To ExpandCount)
      Else
         ReDim Preserve Result(LBound(Result) To UBound(Result) + ExpandCount)
      End If
   End If
   ExpandBlank2List = Result
End Function

' 向 List 末尾添加一个新元素
Function ExpandValue2List(toExpandList, NewValue)
   Dim Result
   Result = ExpandBlank2List(toExpandList, 1)
   Result(UBound(Result)) = NewValue
   ExpandValue2List = Result
End Function

' 将一个 List (NewValueList) 的所有元素追加到另一个 List (toExpandList) 的末尾
Function ExpandList2List(toExpandList, NewValueList)
   Dim Result, ExpandCount As Long, i As Long
   Result = toExpandList
   If IsArray(NewValueList) Then
      If IsArrayNotEmpty(NewValueList) Then
         ExpandCount = DimensionLength(NewValueList)
         Dim OriginalUBound As Long
         If IsArrayNotEmpty(Result) Then OriginalUBound = UBound(Result) Else OriginalUBound = LBound(Result) - 1
         Result = ExpandBlank2List(Result, ExpandCount)
         For i = 0 To ExpandCount - 1
            Result(OriginalUBound + 1 + i) = NewValueList(LBound(NewValueList) + i)
         Next
      End If
   End If
   ExpandList2List = Result
End Function

' 手动实现数组转置功能，用于替代 Application.Transpose
' 以解决 Excel 2007 及以后版本 Transpose 函数对超过 65535 行或列的数组限制问题
Function BigArrayTranspose(toTransposeArray)
   If GetDimension(toTransposeArray) <> 2 Then Exit Function ' 仅支持二维数组转置
   Dim Result()
   Dim L1 As Long, U1 As Long, L2 As Long, U2 As Long
   L1 = LBound(toTransposeArray, 1)
   U1 = UBound(toTransposeArray, 1)
   L2 = LBound(toTransposeArray, 2)
   U2 = UBound(toTransposeArray, 2)
   
   ReDim Result(L2 To U2, L1 To U1) ' 定义转置后的数组维度
   
   Dim i As Long, j As Long
   For i = L1 To U1
      For j = L2 To U2
         Result(j, i) = toTransposeArray(i, j)
      Next
   Next
   BigArrayTranspose = Result
End Function

' 检查输入变量，如果不是数组而是字符串，则尝试按逗号分割成数组
' 主要用于处理函数参数，允许传入数组或逗号分隔的字符串
Public Function CheckList(InputVar)
   Dim Ret
   If IsEmpty(InputVar) Then Exit Function
   If IsArray(InputVar) Then
      Ret = InputVar
   Else
      If VarType(InputVar) = vbString Then
         Ret = Split(InputVar, ",")
      Else
         ' 如果既不是数组也不是字符串，则返回 Empty 或 包含单个元素的数组？
         ReDim Ret(1 To 1)
         Ret(1) = InputVar
      End If
   End If
   CheckList = Ret
End Function
