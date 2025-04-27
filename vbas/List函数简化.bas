Attribute VB_Name = "List函数简化"
Option Explicit

'压入一个元素到list,有副作用
'Position取+/-1表示头尾
Public Function Push(e, lst, Optional Position = -1)
   If Position = 1 Then
      lst = cons(e, lst)  ' 元素添加到列表头部
   Else
      If Not IsList(lst) Then
         ReDim lst(0 To 0)  ' 如果不是列表，则初始化为单元素数组
      Else
         ReDim Preserve lst(0 To UBound(lst) + 1)  ' 扩展数组大小
      End If
      lst(UBound(lst)) = e  ' 元素添加到列表尾部
   End If
End Function

'获得由元素e以及lst的所有元素构成的新List,无副作用
Public Function cons(e, lst)
   Dim Result
   If Not IsList(lst) Then
      ReDim Result(0 To 0)  ' 初始化为单元素数组
      Result(0) = e
   Else
      ReDim Result(LBound(lst) To UBound(lst) + 1)  ' 创建新数组
      Dim i
      Result(LBound(lst)) = e  ' 首位放新元素
      For i = LBound(lst) To UBound(lst)
         Result(i + 1) = lst(i)  ' 复制原列表元素
      Next
   End If
   cons = Result
End Function

'判断是否为有效list,还缺数组维度为1的检测
Public Function IsList(lst) As Boolean
'   If IsEmpty(lst) Then Exit Function
   If Not IsArray(lst) Then Exit Function  ' 必须是数组
   '定义为数组变量的空的list上标为-1,下标为0
   If UBound(lst) < LBound(lst) Then Exit Function  ' 空数组不算有效列表
   IsList = True
End Function

'获得由lst1以及lst2及可能存在的更多的lst所有元素构成的新List,无副作用
Public Function Append(lst1, lst2, ParamArray lst())
   Dim Ret
   If Not IsList(lst1) Then
      Ret = lst2  ' 如果lst1不是有效列表，直接返回lst2
   Else
      Ret = lst1  ' 先将lst1赋值给结果
      If IsList(lst2) Then
         Dim UBoundRet As Long: UBoundRet = UBound(Ret)
         Dim SizeOflst2 As Long: SizeOflst2 = SizeOf(lst2)
         Dim LBoundlst2 As Long: LBoundlst2 = LBound(lst2)
         ReDim Preserve Ret(LBound(Ret) To UBoundRet + SizeOflst2)  ' 扩展数组大小
         Dim i As Long: For i = 1 To SizeOflst2
            Ret(UBoundRet + i) = lst2(LBoundlst2 + i - 1)  ' 复制lst2元素到结果
         Next
      End If
   End If
   Dim MoreList: MoreList = lst
   If IsList(MoreList) Then
      If Not IsEmpty(MoreList(LBound(MoreList))) Then
         Ret = Append(Ret, car(MoreList), cdr(MoreList))  ' 递归处理更多的列表
      End If
   End If
   Append = Ret
End Function

'得到list的元素个数
Public Function SizeOf(lst)
   If Not IsList(lst) Then Exit Function
   SizeOf = UBound(lst) - LBound(lst) + 1
End Function

'首个元素
Public Function car(lst)
    car = nth(lst, 1)  ' 获取第一个元素
End Function

'取指定位置的元素,正值从前到后,负值从后到前
Public Function nth(lst, ListSequence)
   If Not IsList(lst) Then Exit Function
   If ListSequence = 0 Then Exit Function  ' 序号0无效
   Dim myIndex, IsVaildIndex As Boolean
   If ListSequence < 0 Then
      myIndex = UBound(lst) + ListSequence + 1  ' 负数表示从末尾数起
      IsVaildIndex = (myIndex >= LBound(lst))
   Else
      myIndex = LBound(lst) + ListSequence - 1  ' 正数表示从开始数起
      IsVaildIndex = (myIndex <= UBound(lst))
   End If
   If IsVaildIndex Then nth = lst(myIndex)
End Function

'除了首个元素之外的元素构造的list
Public Function cdr(lst)
   If Not IsList(lst) Then Exit Function
   If UBound(lst) = LBound(lst) Then Exit Function  ' 单元素列表返回空
   Dim i, Result
   ReDim Result(LBound(lst) + 1 To UBound(lst))
   For i = LBound(lst) + 1 To UBound(lst)
       Result(i) = lst(i)  ' 复制除第一个元素外的所有元素
   Next
   cdr = Result
End Function
