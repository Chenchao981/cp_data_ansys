Attribute VB_Name = "List������"
Option Explicit

'ѹ��һ��Ԫ�ص�list,�и�����
'Positionȡ+/-1��ʾͷβ
Public Function Push(e, lst, Optional Position = -1)
   If Position = 1 Then
      lst = cons(e, lst)  ' Ԫ����ӵ��б�ͷ��
   Else
      If Not IsList(lst) Then
         ReDim lst(0 To 0)  ' ��������б����ʼ��Ϊ��Ԫ������
      Else
         ReDim Preserve lst(0 To UBound(lst) + 1)  ' ��չ�����С
      End If
      lst(UBound(lst)) = e  ' Ԫ����ӵ��б�β��
   End If
End Function

'�����Ԫ��e�Լ�lst������Ԫ�ع��ɵ���List,�޸�����
Public Function cons(e, lst)
   Dim Result
   If Not IsList(lst) Then
      ReDim Result(0 To 0)  ' ��ʼ��Ϊ��Ԫ������
      Result(0) = e
   Else
      ReDim Result(LBound(lst) To UBound(lst) + 1)  ' ����������
      Dim i
      Result(LBound(lst)) = e  ' ��λ����Ԫ��
      For i = LBound(lst) To UBound(lst)
         Result(i + 1) = lst(i)  ' ����ԭ�б�Ԫ��
      Next
   End If
   cons = Result
End Function

'�ж��Ƿ�Ϊ��Чlist,��ȱ����ά��Ϊ1�ļ��
Public Function IsList(lst) As Boolean
'   If IsEmpty(lst) Then Exit Function
   If Not IsArray(lst) Then Exit Function  ' ����������
   '����Ϊ��������Ŀյ�list�ϱ�Ϊ-1,�±�Ϊ0
   If UBound(lst) < LBound(lst) Then Exit Function  ' �����鲻����Ч�б�
   IsList = True
End Function

'�����lst1�Լ�lst2�����ܴ��ڵĸ����lst����Ԫ�ع��ɵ���List,�޸�����
Public Function Append(lst1, lst2, ParamArray lst())
   Dim Ret
   If Not IsList(lst1) Then
      Ret = lst2  ' ���lst1������Ч�б�ֱ�ӷ���lst2
   Else
      Ret = lst1  ' �Ƚ�lst1��ֵ�����
      If IsList(lst2) Then
         Dim UBoundRet As Long: UBoundRet = UBound(Ret)
         Dim SizeOflst2 As Long: SizeOflst2 = SizeOf(lst2)
         Dim LBoundlst2 As Long: LBoundlst2 = LBound(lst2)
         ReDim Preserve Ret(LBound(Ret) To UBoundRet + SizeOflst2)  ' ��չ�����С
         Dim i As Long: For i = 1 To SizeOflst2
            Ret(UBoundRet + i) = lst2(LBoundlst2 + i - 1)  ' ����lst2Ԫ�ص����
         Next
      End If
   End If
   Dim MoreList: MoreList = lst
   If IsList(MoreList) Then
      If Not IsEmpty(MoreList(LBound(MoreList))) Then
         Ret = Append(Ret, car(MoreList), cdr(MoreList))  ' �ݹ鴦�������б�
      End If
   End If
   Append = Ret
End Function

'�õ�list��Ԫ�ظ���
Public Function SizeOf(lst)
   If Not IsList(lst) Then Exit Function
   SizeOf = UBound(lst) - LBound(lst) + 1
End Function

'�׸�Ԫ��
Public Function car(lst)
    car = nth(lst, 1)  ' ��ȡ��һ��Ԫ��
End Function

'ȡָ��λ�õ�Ԫ��,��ֵ��ǰ����,��ֵ�Ӻ�ǰ
Public Function nth(lst, ListSequence)
   If Not IsList(lst) Then Exit Function
   If ListSequence = 0 Then Exit Function  ' ���0��Ч
   Dim myIndex, IsVaildIndex As Boolean
   If ListSequence < 0 Then
      myIndex = UBound(lst) + ListSequence + 1  ' ������ʾ��ĩβ����
      IsVaildIndex = (myIndex >= LBound(lst))
   Else
      myIndex = LBound(lst) + ListSequence - 1  ' ������ʾ�ӿ�ʼ����
      IsVaildIndex = (myIndex <= UBound(lst))
   End If
   If IsVaildIndex Then nth = lst(myIndex)
End Function

'�����׸�Ԫ��֮���Ԫ�ع����list
Public Function cdr(lst)
   If Not IsList(lst) Then Exit Function
   If UBound(lst) = LBound(lst) Then Exit Function  ' ��Ԫ���б��ؿ�
   Dim i, Result
   ReDim Result(LBound(lst) + 1 To UBound(lst))
   For i = LBound(lst) + 1 To UBound(lst)
       Result(i) = lst(i)  ' ���Ƴ���һ��Ԫ���������Ԫ��
   Next
   cdr = Result
End Function
