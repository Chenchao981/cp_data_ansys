VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "clsRegEx"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit
'==============================================
' 类模块: clsRegEx
' 功能: 封装 VBScript.RegExp 对象，提供正则表达式相关操作
' 更新日期: 2015-11-29
' 注意事项: 依赖 Microsoft VBScript Regular Expressions 库
'==============================================

' 定义一个常用的数字正则表达式模式（整数、小数、科学计数法）
Private Const REG_NUMBER = "\d+(\.\d+)?(e[\+\-]\d+)?"

' VBScript 正则表达式对象实例
Private objRegEx As Object
' 当前操作的目标字符串
Private myString

' 内部函数，用于替换自定义占位符（如 _NUMBER_）为实际的正则表达式模式
Private Function ChangePattern(toChangePattern) As String
   Dim Ret As String
   Ret = VBA.Replace(toChangePattern, "_NUMBER_", REG_NUMBER)
   ChangePattern = Ret
End Function

' 类初始化时，创建 RegExp 对象并设置默认选项
Private Sub Class_Initialize()
   Set objRegEx = CreateObject("VBScript.RegExp")
   Call Construct ' 调用构造函数设置默认属性
End Sub

' 类终止时，释放 RegExp 对象
Private Sub Class_Terminate()
    Set objRegEx = Nothing
End Sub

' 公开方法，用于配置 RegExp 对象的属性（全局匹配、忽略大小写、多行模式）
Public Sub Construct(Optional boolGlobal As Boolean = True, _
                     Optional IgnoreCase As Boolean = True, _
                     Optional MultiLine As Boolean = True)
   With objRegEx
      .Global = boolGlobal        ' 设置是否全局匹配
      .IgnoreCase = IgnoreCase    ' 设置是否忽略大小写
      .MultiLine = MultiLine      ' 设置是否多行模式
   End With
End Sub

' 清除字符串中匹配的部分
' 注意：此函数实现可能有误，Replace 第一个参数应为目标字符串
Public Function Clear(sPattern, Optional newString)
    Clear = Replace(sPattern, "", myString)
End Function

' 在目标字符串 (myString) 中查找匹配 sPattern 的部分，并替换为 sReplace
Public Function Replace(sPattern, sReplace, Optional newString)
   Dim Ret
   ' 先测试是否存在匹配项
   If TestPattern(sPattern, newString) Then
      Ret = objRegEx.Replace(myString, sReplace)  ' 执行替换操作
   Else
      Ret = myString ' 没有匹配项则返回原字符串
   End If
   Replace = Ret
End Function

' 执行正则表达式匹配，返回包含所有匹配结果的 MatchCollection 对象
Public Function Matches(sPattern, Optional newString) As Object
    ' 先测试是否存在匹配项
    If TestPattern(sPattern, newString) Then Set Matches = objRegEx.Execute(myString)
End Function

' 设置或更新当前要操作的目标字符串
Public Property Let OperatString(ByVal newString)
    myString = newString
End Property

' 获取第一个匹配项的值
Public Function FirstMatchValue(sPattern, Optional newString)
   FirstMatchValue = GetFirstMatchesInfo(sPattern, "Value", newString)
End Function

' 获取第一个匹配项的第一个子匹配 (Submatch) 的值
Public Function FirstSubMatchValue(sPattern, Optional newString)
    FirstSubMatchValue = GetFirstMatchesInfo(sPattern, "FirstSubmatch", newString)
End Function

' 获取第一个匹配项的最后一个子匹配 (Submatch) 的值
Public Function LastSubMatchValue(sPattern, Optional newString)
   LastSubMatchValue = GetFirstMatchesInfo(sPattern, "LastSubMatch", newString)
End Function

' 内部函数，根据 InfoType 获取第一个匹配项的相关信息 (Value, FirstSubmatch, LastSubMatch)
Private Function GetFirstMatchesInfo(sPattern, InfoType, Optional newString)
    Dim m As Object, Ret
    Set m = Matches(sPattern, newString) ' 获取匹配结果集合
    If Not m Is Nothing Then
      If m.Count > 0 Then ' 确保至少有一个匹配项
         With m(0) ' 处理第一个匹配项
            Select Case InfoType
            Case "Value"
               Ret = .Value         ' 返回完整匹配
            Case "FirstSubmatch"
               If .submatches.Count > 0 Then Ret = .submatches(0)  ' 返回第一个子匹配
            Case "LastSubMatch"
               If .submatches.Count > 0 Then Ret = .submatches(.submatches.Count - 1)  ' 返回最后一个子匹配
            End Select
         End With
      End If
   End If
   GetFirstMatchesInfo = Ret
End Function

' 测试目标字符串是否匹配给定的正则表达式模式
Public Function TestPattern(sPattern, Optional newString) As Boolean
    ' 如果提供了 newString，则更新目标字符串
    If Not IsMissing(newString) Then myString = newString
    ' 设置正则表达式模式，替换自定义占位符
    objRegEx.Pattern = ChangePattern(sPattern)
    ' 执行测试
    TestPattern = objRegEx.test(myString)
End Function

' 将一个字符串列表 (sList)，根据 SplitPattern 进行拆分，并将结果存入二维数组
' AheadIsDetail 参数控制拆分出的子匹配是放在原字符串前面还是后面
Public Function SplitList2Array(sList, SplitPattern, _
                                Optional AheadIsDetail As Boolean = True)
   Dim Ret
   ' 检查输入是否为有效的列表 (数组)
   If Not IsList(sList) Then Exit Function
   Dim lbd: lbd = LBound(sList)
   Dim ubd: ubd = UBound(sList)
   ' 计算子匹配数据开始填充的列索引
   Dim DetailStart: DetailStart = lbd + IIf(AheadIsDetail, 0, 2)
   Dim MatchFillPos As Long ' 存储完整匹配项的列索引
   Dim OriginalFillPos As Long ' 存储原始字符串的列索引
   
   objRegEx.Pattern = ChangePattern(SplitPattern)
   Dim i: For i = lbd To ubd
      Dim m As Object: Set m = objRegEx.Execute(sList(i))
      If Not m Is Nothing Then
         If m.Count > 0 Then
            With m(0) ' 只处理第一个匹配结果
               Dim DataCount: DataCount = .submatches.Count
               ' 如果是第一次找到匹配项，则初始化结果数组 Ret 的维度
               If IsEmpty(Ret) Then
                  ReDim Ret(lbd To ubd, lbd To lbd + DataCount + 1) ' 行数为原列表大小，列数为 子匹配数 + 完整匹配 + 原字符串
                  ' 根据 AheadIsDetail 计算存储完整匹配和原字符串的列位置
                  MatchFillPos = IIf(AheadIsDetail, DetailStart + DataCount, lbd + 1)
                  OriginalFillPos = IIf(AheadIsDetail, DetailStart + DataCount + 1, lbd)
               End If
               ' 填充子匹配项
               Dim j: For j = 0 To DataCount - 1
                  Ret(i, DetailStart + j) = .submatches(j)
               Next
               ' 填充完整匹配项和原始字符串
               Ret(i, MatchFillPos) = .Value
               Ret(i, OriginalFillPos) = sList(i)
            End With
         End If
      End If
   Next
   SplitList2Array = Ret
End Function

