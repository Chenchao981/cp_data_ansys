VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "clsShowInfo"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit

' 用于存储信息及其显示次数，避免重复提示
Dim ShowInfoDic As Object

' 记录信息 s 的显示次数，如果已存在则次数加 1
Private Function GetInfoRepeatTimes(s As String) As Integer
   Dim Ret As Integer: Ret = 1
   If ShowInfoDic.exists(s) Then Ret = ShowInfoDic(s) + 1
   ShowInfoDic(s) = Ret
   GetInfoRepeatTimes = Ret
End Function

' 显示提示信息，但限制同一信息的最大重复显示次数
Public Function PromptInfo(ShowInfo, _
                           Optional Title As String = "提示", _
                           Optional RepeatCountMax = 10)
   
   Dim s As String: s = Info2Str(ShowInfo) ' 将传入的信息统一转换为字符串
   ' 检查信息显示次数是否超过限制
   If GetInfoRepeatTimes(s) <= RepeatCountMax Then
      MsgBox s, vbInformation, Title
   End If
End Function

' 内部函数，用于构建并显示包含错误信息和可选解决方案的对话框
Private Function ExceptionPrompt(ErrInfo, Title, OCAP)
   Dim s
   Push "错误现象:" & vbCrLf & String(12, "-"), s ' 添加错误标题
   Push Info2Str(ErrInfo), s ' 添加错误详情
   ' 如果提供了 OCAP (推荐解决方案)，则添加
   If Not IsError(OCAP) Then
      Push vbCrLf & "推荐的解决方案:" & vbCrLf & String(21, "-"), s
      Push Info2Str(OCAP), s
   End If
   ' 根据标题是否包含"终止"来决定使用 vbCritical 还是 vbExclamation 图标
   MsgBox Join(s, vbCrLf), IIf(InStr(Title, "终止"), vbCritical, vbExclamation), "警告"
End Function

' 公开方法，显示警告信息（非终止性）
Public Function ErrAlarm(ErrInfo, Optional Title = "警告", Optional OCAP)
   ExceptionPrompt ErrInfo, Title, OCAP
End Function

' 公开方法，显示错误信息并终止宏的执行
Public Function ErrStop(ErrInfo, Optional Title = "异常终止", Optional OCAP)
   ExceptionPrompt ErrInfo, Title, OCAP
   End ' 终止宏执行
End Function

' 类初始化时创建字典对象
Private Sub Class_Initialize()
   Set ShowInfoDic = CreateObject("scripting.dictionary")
End Sub

' 类终止时释放字典对象
Private Sub Class_Terminate()
 Set ShowInfoDic = Nothing
End Sub
