Attribute VB_Name = "������䵽������"
Option Explicit

' ��һ�� List (һά����򶺺ŷָ��ַ���) ��䵽ָ������ʼ��Ԫ�� (StartCell)
' HorizontalFlag: True (Ĭ��) ��ˮƽ��䣬False ��ֱ���
Public Function ListFill2Rng(StartCell As Range, _
                             toFillList, _
                             Optional HorizontalFlag As Boolean = True) As Range
   Dim myList, Result As Range
   myList = CheckList(toFillList) ' ȷ������������
   If Not IsArrayNotEmpty(myList) Then Exit Function ' �������Ϊ�գ����˳�
   
   Dim ListLen As Long: ListLen = DimensionLength(myList)
   If ListLen = 0 Then Exit Function
   
   On Error Resume Next ' �������ʱ���ܷ����Ĵ��� (�絥Ԫ�񱣻�)
   If HorizontalFlag Then
      Set Result = StartCell.Resize(1, ListLen)
      Result.Value = myList ' ֱ�Ӹ�ֵ���
   Else
      Set Result = StartCell.Resize(ListLen, 1)
      Result.Value = Application.Transpose(myList) ' ��ֱ�����Ҫת��
   End If
   If Err.Number <> 0 Then Set Result = Nothing ' ����������� Nothing
   On Error GoTo 0
   
   Set ListFill2Rng = Result
End Function

' ��һ����ά���� (DataArray) ��䵽ָ������ʼ��Ԫ�� (StartCell)
' ArrayTransPoseFlag: True ����ת����������䣬False (Ĭ��) ��ֱ�����
Public Function FillArray2Rng(StartCell As Range, _
                          DataArray, _
                          Optional ArrayTransPoseFlag As Boolean = False) As Range
   Dim Result As Range, Rows As Long, Cols As Long
   
   If GetDimension(DataArray) = 0 Then Exit Function ' �������Ϊ�գ����˳�
   Rows = DimensionLength(DataArray, 1)
   Cols = DimensionLength(DataArray, 2)
   If Cols = 0 Then Cols = 1 ' ����һά������������Ϊ N�� x 1��
   
   If Rows * Cols = 0 Then Exit Function ' �������������Ϊ0�����˳�
   
   On Error Resume Next ' �������ʱ���ܷ����Ĵ���
   If ArrayTransPoseFlag Then
      Set Result = StartCell.Resize(Cols, Rows)
      ' ����Ƿ���Ҫʹ�� BigArrayTranspose ������ Transpose �� 65535 ����
      If Rows > 65535 Or Cols > 65535 Then
         Result.Value = BigArrayTranspose(DataArray)
      Else
         Result.Value = Application.Transpose(DataArray)
      End If
   Else
      Set Result = StartCell.Resize(Rows, Cols)
      Result.Value = DataArray
   End If
   If Err.Number <> 0 Then Set Result = Nothing ' ����������� Nothing
   On Error GoTo 0
   
   Set FillArray2Rng = Result
End Function

'============= ������λ���� =============

' ����ָ���������У��� A1 ��ʼ�ĵ�ǰ���� (CurrentRegion) �·��ĵ�һ���հ׵�Ԫ�� (A��)
Public Function SearchFirstBlankCell(toCheckSheet As Worksheet) As Range
   On Error Resume Next
   Set SearchFirstBlankCell = toCheckSheet.Cells(toCheckSheet.Range("a1").CurrentRegion.Rows.Count + 1, 1)
   On Error GoTo 0
End Function

' ��ȡָ���������У��� A1 ��ʼ�ĵ�ǰ�����������
Public Function SheetUsedRowsFromA1(toCheckSheet As Worksheet) As Long
   On Error Resume Next
   SheetUsedRowsFromA1 = toCheckSheet.Range("a1").CurrentRegion.Rows.Count
   On Error GoTo 0
End Function

' ��ȡָ���������У��� A1 ��ʼ�ĵ�ǰ�����������
Public Function SheetUsedColsFromA1(toCheckSheet As Worksheet) As Long
   On Error Resume Next
   SheetUsedColsFromA1 = toCheckSheet.Range("a1").CurrentRegion.Columns.Count
   On Error GoTo 0
End Function


' (�˺����ƺ�δ����Ŀ��ʹ��)
' �����ݱ� (DataTable) �ͱ�ͷ (HeadList) ��ʾ��ָ�������� (ResultSheet) ���¹�������
Public Function DisplayInfo(DataTable, HeadList, Optional ResultSheet As Worksheet, Optional ArrayTransPoseFlag As Boolean = False)
   Dim TargetSheet As Worksheet
   If ResultSheet Is Nothing Then
      Dim w As Workbook: Set w = Workbooks.Add
      If w Is Nothing Then Exit Function ' ����ʧ�����˳�
      Set TargetSheet = w.Worksheets(1)
   Else
      Set TargetSheet = ResultSheet
   End If
   
   On Error Resume Next
   With TargetSheet
      .Cells.ClearContents ' ���ԭ������ (��������!)
      ListFill2Rng .Range("a1"), HeadList
      FillArray2Rng .Range("a2"), DataTable, ArrayTransPoseFlag
   End With
   If Err.Number <> 0 Then
       gShow.ErrAlarm "��ʾ��Ϣʧ��: " & Err.Description
   End If
   On Error GoTo 0
End Function
