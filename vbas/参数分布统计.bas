Attribute VB_Name = "�����ֲ�ͳ��"
Option Explicit

' ����ÿ�� Wafer ÿ��������ͳ����Ϣ (Avg, Std, Median, RobustStd)�����������䵽 "Summary" ������
Public Sub mySummary(w As Workbook, TestInfo As CPLot)

   ' 1. ��ȡ��ǰ��Ʒ�Ĳ������㷶Χ����
   Dim ScopeRng As Range: Set ScopeRng = GetProductScopeDefine(TestInfo.Product)
   If ScopeRng Is Nothing Then
       gShow.PromptInfo "δ�� SCOPE_SHEET ���ҵ���Ʒ " & TestInfo.Product & " �ļ��㷶Χ���壬��ʹ��ȫ�����ݽ���ͳ�Ƽ��㡣"
   End If
   
   Dim SummarySheet As Worksheet: Set SummarySheet = w.Worksheets("Summary")
   If SummarySheet Is Nothing Then
       gShow.ErrStop "�޷��ҵ� Summary ������"
       Exit Sub
   End If
   
   With SummarySheet
      .Cells.ClearContents ' ��չ�����ԭ������
      ' 2. д���ͷ
      .Range("a1:c1").Value = Array("Item", "Spec", "Stat")
      
      ' 3. ����ÿ�� Wafer
      Dim WaferIndex As Long
      For WaferIndex = 1 To TestInfo.WaferCount
         Application.StatusBar = "����ͳ��������..." & TestInfo.Wafers(WaferIndex).WaferId
         .Cells(1, WaferIndex + 3).Value = TestInfo.Wafers(WaferIndex).WaferId & "#" ' �ڵ�һ��д�� Wafer ID
         
         Dim r As Long: r = 2 ' ��ǰ����д�����ʼ�к�
         Dim i As Long ' ��������
         For i = 1 To TestInfo.ParamCount
            ' 4. ���ڴ����һ�� Wafer ʱ��д�������Ϣ (Item, Spec, Stat ����)
            If WaferIndex = 1 Then
               .Cells(r, 1).Value = TestInfo.Params(i).Id & "[" & TestInfo.Params(i).Unit & "]" ' Item ��
               Dim SpecInfo As String: SpecInfo = TestInfo.Params(i).SL & " - " & TestInfo.Params(i).SU
               If IsArray(TestInfo.Params(i).TestCond) Then
                  If UBound(TestInfo.Params(i).TestCond) >= LBound(TestInfo.Params(i).TestCond) Then
                      SpecInfo = SpecInfo & "@" & TestInfo.Params(i).TestCond(LBound(TestInfo.Params(i).TestCond)) ' ��ӵ�һ����������
                  End If
               End If
               .Cells(r, 2).Value = SpecInfo ' Spec ��
               ' Stat ��д��ͳ�������� (Avg, Std, Median, RobustStd)
               .Cells(r, 3).Value = "Avg."
               .Cells(r + 1, 3).Value = "Std"
               .Cells(r + 2, 3).Value = "Median"
               .Cells(r + 3, 3).Value = "RobustStd"
               ' ���� Item �� Spec ��Ϣ���·���Ӧ��ͳ������
               .Range(.Cells(r, 1), .Cells(r, 2)).Copy .Range(.Cells(r + 1, 1), .Cells(r + 3, 2))
            End If
            
            ' 5. ��ȡ��ǰ Wafer ��ǰ������ԭʼ����
            Dim toFilterData: toFilterData = TestInfo.Wafers(WaferIndex).ChipDatas(i)
            Dim myData ' ���ڴ洢ɸѡ�����ݵı���
            
            ' 6. ���� ScopeRng ɸѡ����
            If ScopeRng Is Nothing Then ' ���δ���巶Χ����ʹ��ȫ������
               myData = toFilterData
            Else
               ' FilterData �������� ScopeRng �ж����������ɸѡ����
               ' ColIndex ��Ҫ��Ӧ ScopeRng �е��У�������� ScopeRng ������ Params ��Ӧ���Ҵӵ�3�п�ʼ?
               ' ע�⣺ԭ���� i + 2 ������Ҫ���� ScopeRng ��ʵ�ʽṹ����
               myData = FilterData(toFilterData, ScopeRng, i + 2)
            End If
            
            ' 7. ����ͳ������д�뵥Ԫ��
            On Error Resume Next ' ����ͳ�ƺ������ܲ����Ĵ��� (�� StDev ������2�����ݵ�)
            If Not IsArray(myData) Or GetDimension(myData) = 0 Then
               .Cells(r, WaferIndex + 3).Value = "(����Ч����)" ' ɸѡ��������
            ElseIf DimensionLength(myData) < 2 Then ' ���ݵ�̫���޷����� StDev
               .Cells(r, WaferIndex + 3).Value = WorksheetFunction.Average(myData)
               .Cells(r + 1, WaferIndex + 3).Value = "(���ݲ���)"
               .Cells(r + 2, WaferIndex + 3).Value = WorksheetFunction.Median(myData)
               .Cells(r + 3, WaferIndex + 3).Value = "(���ݲ���)"
            ElseIf DimensionLength(myData) < 4 Then ' ���ݵ�̫���޷����� Quartile
               .Cells(r, WaferIndex + 3).Value = WorksheetFunction.Average(myData)
               .Cells(r + 1, WaferIndex + 3).Value = WorksheetFunction.StDev_S(myData) ' ʹ�� StDev_S (������׼��)
               .Cells(r + 2, WaferIndex + 3).Value = WorksheetFunction.Median(myData)
               .Cells(r + 3, WaferIndex + 3).Value = "(���ݲ���)"
            Else ' �����㹻��������ͳ����
               .Cells(r, WaferIndex + 3).Value = WorksheetFunction.Average(myData)
               .Cells(r + 1, WaferIndex + 3).Value = WorksheetFunction.StDev_S(myData)
               .Cells(r + 2, WaferIndex + 3).Value = WorksheetFunction.Median(myData)
               ' �����Ƚ���׼�� (Robust Standard Deviation) = IQR / 1.34898
               .Cells(r + 3, WaferIndex + 3).Value = (WorksheetFunction.Quartile_Inc(myData, 3) _
                                                   - WorksheetFunction.Quartile_Inc(myData, 1)) / 1.34898
            End If
            On Error GoTo 0
            
            r = r + 4 ' �ƶ�����һ��������д���� (ÿ������ռ 4 ��)
         Next i
      Next WaferIndex
      
      ' 8. ��ʽ�� Summary ������
      .UsedRange.Columns.AutoFit ' �Զ������п�
      '.UsedRange.AutoFilter ' ��ѡ������Զ�ɸѡ����
   End With
End Sub

' ����ָ���ķ�Χ (ScopeRng) ɸѡ���� (toFilterData)
' ColIndex: ָʾ�� ScopeRng �в��������޵������� (���� 1)
Private Function FilterData(toFilterData, ScopeRng As Range, ColIndex As Long)
   If GetDimension(toFilterData) = 0 Then Exit Function ' �����������Ϊ�����˳�
   
   On Error Resume Next
   Dim ScreenDataLowLimit: ScreenDataLowLimit = ScopeRng.Cells(2, ColIndex).Value ' ��ȡ���� (�� 2 ��)
   Dim ScreenDataHighLimit: ScreenDataHighLimit = ScopeRng.Cells(3, ColIndex).Value ' ��ȡ���� (�� 3 ��)
   If Err.Number <> 0 Then Exit Function ' �����ȡ�����޳��� (���� ColIndex ������Χ)����ɸѡ
   On Error GoTo 0
   
   Dim IsLowLimitValid As Boolean: IsLowLimitValid = IsNumeric(ScreenDataLowLimit)
   Dim IsHighLimitValid As Boolean: IsHighLimitValid = IsNumeric(ScreenDataHighLimit)
   
   ' ��������޶���Ч����ɸѡ������ԭʼ����
   If Not IsLowLimitValid And Not IsHighLimitValid Then FilterData = toFilterData: Exit Function
   
   Dim ResultList As Object: Set ResultList = CreateObject("System.Collections.ArrayList") ' ʹ�� ArrayList ��̬�洢ɸѡ���
   Dim item As Variant
   For Each item In toFilterData
      If IsNumeric(item) Then ' ֻ������ֵ������
         Dim Val As Double: Val = CDbl(item)
         Dim KeepFlag As Boolean: KeepFlag = True
         If IsHighLimitValid Then
             If Val >= ScreenDataHighLimit Then KeepFlag = False
         End If
         If KeepFlag And IsLowLimitValid Then
             If Val <= ScreenDataLowLimit Then KeepFlag = False
         End If
         
         If KeepFlag Then ResultList.Add Val
      End If
   Next
   
   ' �� ArrayList ת��Ϊ VBA ���鷵��
   If ResultList.Count > 0 Then
      FilterData = ResultList.ToArray
   Else
      FilterData = Empty ' ���û�������������������� Empty
   End If
   
End Function

