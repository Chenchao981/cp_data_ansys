Attribute VB_Name = "ͨ�������������"
Option Explicit

' ��ģ���ṩͨ�õ����飨�ڴ˳�Ϊ List, Vector, Table����������
' ����: һά����Ϊ List, ֻ��1�еĶ�ά����Ϊ Vector, ��ά����Ϊ Table

' ���� Windows API �������ڻ�ȡ����ά�� (ע��: �� Variant ���͵Ķ�̬���������Ч)
Private Declare Function SafeArrayGetDim Lib "oleaut32.dll" (ByRef saArray() As Any) As Long

'========== ����״̬ʶ���� ================

' �ж������Ƿ�Ϊ�� (δ��ʼ���� ReDim ��δ��ֵ)
' ʹ�� GetDimension ����ͨ�����������ж�
Function IsArrayEmpty(toCheckArray) As Boolean
   IsArrayEmpty = (GetDimension(toCheckArray) = 0)
End Function

' �ж������Ƿ�ǿ� (�ѳ�ʼ����������һ��ά��)
Function IsArrayNotEmpty(toCheckArray) As Boolean
   IsArrayNotEmpty = (GetDimension(toCheckArray) > 0)
End Function

' ��ȡ�����ά������
' ͨ�����Է��ʲ�ͬά�ȵ� UBound ��ȷ��������� 60 ά
' �� Variant ����������Ч
Function GetDimension(toCheckArray)
   Dim Result
   Dim i As Long
   On Error Resume Next
   For i = 1 To 60 ' VBA �������֧�� 60 ά
      Result = UBound(toCheckArray, i)
      If Err.Number <> 0 Then Exit For ' ������� UBound ����˵��ά�Ȳ�����
   Next
   On Error GoTo 0
   GetDimension = i - 1 ' ʵ��ά�������һ���ɹ����ʵ�����
End Function

' ��ȡ����ָ��ά�ȵĳ��� (Ԫ�ظ���)
Public Function DimensionLength(toCheckArray, Optional Dimension = 1)
   If GetDimension(toCheckArray) >= Dimension Then
      On Error Resume Next
      DimensionLength = UBound(toCheckArray, Dimension) - LBound(toCheckArray, Dimension) + 1
      If Err.Number <> 0 Then DimensionLength = 0 ' ���� LBound > UBound �Ŀ��������
      On Error GoTo 0
   Else
      DimensionLength = 0 ' ά�Ȳ�����
   End If
End Function

' ��ȫ�ظ������������ֵ
' ���Դ�Ƕ�����ʹ�� Set������ֱ�Ӹ�ֵ
Sub ArrayValueCopy(Target, Source)
   If IsObject(Source) Then
      Set Target = Source
   Else
      Target = Source
   End If
End Sub

'=========== ��չ�������� ===============

' ��չһ�� List (һά����) �Ĵ�С������ָ�������Ŀ�Ԫ��
Function ExpandBlank2List(toExpandList, Optional ExpandCount = 1)
   Dim Result
   Result = toExpandList
   If ExpandCount > 0 Then
      If GetDimension(Result) = 0 Then ' ���ԭ����Ϊ��
         ReDim Result(1 To ExpandCount)
      Else
         ReDim Preserve Result(LBound(Result) To UBound(Result) + ExpandCount)
      End If
   End If
   ExpandBlank2List = Result
End Function

' �� List ĩβ���һ����Ԫ��
Function ExpandValue2List(toExpandList, NewValue)
   Dim Result
   Result = ExpandBlank2List(toExpandList, 1)
   Result(UBound(Result)) = NewValue
   ExpandValue2List = Result
End Function

' ��һ�� List (NewValueList) ������Ԫ��׷�ӵ���һ�� List (toExpandList) ��ĩβ
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

' �ֶ�ʵ������ת�ù��ܣ�������� Application.Transpose
' �Խ�� Excel 2007 ���Ժ�汾 Transpose �����Գ��� 65535 �л��е�������������
Function BigArrayTranspose(toTransposeArray)
   If GetDimension(toTransposeArray) <> 2 Then Exit Function ' ��֧�ֶ�ά����ת��
   Dim Result()
   Dim L1 As Long, U1 As Long, L2 As Long, U2 As Long
   L1 = LBound(toTransposeArray, 1)
   U1 = UBound(toTransposeArray, 1)
   L2 = LBound(toTransposeArray, 2)
   U2 = UBound(toTransposeArray, 2)
   
   ReDim Result(L2 To U2, L1 To U1) ' ����ת�ú������ά��
   
   Dim i As Long, j As Long
   For i = L1 To U1
      For j = L2 To U2
         Result(j, i) = toTransposeArray(i, j)
      Next
   Next
   BigArrayTranspose = Result
End Function

' ���������������������������ַ��������԰����ŷָ������
' ��Ҫ���ڴ���������������������򶺺ŷָ����ַ���
Public Function CheckList(InputVar)
   Dim Ret
   If IsEmpty(InputVar) Then Exit Function
   If IsArray(InputVar) Then
      Ret = InputVar
   Else
      If VarType(InputVar) = vbString Then
         Ret = Split(InputVar, ",")
      Else
         ' ����Ȳ�������Ҳ�����ַ������򷵻� Empty �� ��������Ԫ�ص����飿
         ReDim Ret(1 To 1)
         Ret(1) = InputVar
      End If
   End If
   CheckList = Ret
End Function
