Attribute VB_Name = "�������㷶Χ����"
Option Explicit

' ���ݲ�Ʒ���� (ProductName) �� SCOPE_SHEET �������в��Ҳ����ض�Ӧ�Ĳ������㷶Χ��������
' SCOPE_SHEET �ṹԤ�ڣ�
'   - A �дӵ� 2 �п�ʼ�ǲ�Ʒ�����б�
'   - ÿ����Ʒ���ƶ�Ӧһ�У����м��·����� (������) �����˸ò�Ʒ�¸��������ļ��㷶Χ
'   - ��һ��ͨ���ǲ������ƻ�������ʶ
'   - �ڶ��� (���Ʒ����ͬ�е���һ��) �Ǽ��㷶Χ����
'   - ������ (��Ʒ�����е�������) �Ǽ��㷶Χ����
' ����ֵ: һ������������ʶ�С������к������й� 3 �����ݵ� Range ��������Ҳ�����Ʒ���ƣ��򷵻� Nothing
Public Function GetProductScopeDefine(ProductName) As Range
   If Len(ProductName) = 0 Then Exit Function ' ��Ʒ����Ϊ�����˳�
   
   Dim ProductRow As Long: ProductRow = 0 ' ��ʼ���ҵ��Ĳ�Ʒ�����к�
   Dim ScopeWs As Worksheet: Set ScopeWs = SCOPE_SHEET
   If ScopeWs Is Nothing Then
       gShow.ErrAlarm "�޷����ʲ������㷶Χ���幤���� (SCOPE_SHEET)��"
       Exit Function
   End If
   
   On Error Resume Next
   Dim x: x = ScopeWs.Range("a1").CurrentRegion.Value ' ��ȡ������Χ���������
   If Err.Number <> 0 Or Not IsArray(x) Then
       gShow.ErrAlarm "��ȡ�������㷶Χ���������ʧ�ܡ�"
       Exit Function
   End If
   On Error GoTo 0
   
   ' �ӵڶ��п�ʼ���Ҳ�Ʒ���� (���Դ�Сд��ǰ��ո�)
   Dim i: For i = 2 To UBound(x, 1)
      If LCase(Trim(x(i, 1))) = LCase(Trim(ProductName)) Then
         ProductRow = i
         Exit For
      End If
   Next
   
   ' ����ҵ��˲�Ʒ���� (ProductRow > 0)
   If ProductRow > 0 Then
       ' ���ذ���������ʶ�С������С������е� Range ����
       ' ���ص������Ǵ� ��Ʒ�����е���һ�� (ProductRow - 1) ��ʼ���� 3 �У��������ȡ������һ��
       Set GetProductScopeDefine = ScopeWs.Cells(ProductRow - 1, 1).Resize(3, UBound(x, 2))
   Else
       ' ���û�ҵ������� Nothing (���÷���Ҫ��������)
       Set GetProductScopeDefine = Nothing
   End If
   
End Function
