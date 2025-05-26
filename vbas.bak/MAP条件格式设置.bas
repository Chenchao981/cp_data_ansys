Attribute VB_Name = "MAP������ʽ����"
Option Explicit

' Ϊ���ݷ�Χ����������ʽ��������ʾ��ͬ��Bin��ɫ
Public Function SetBinMapFormatCondtions(DataRng As Range, BinColorDic As Object)
   With BinColorDic
      Dim myBins: myBins = .Keys     ' ��ȡ����Binֵ
      Dim myColors: myColors = .items  ' ��ȡ��Ӧ����ɫ
   End With
   
   Dim myCondition As FormatCondition: Set myCondition = DataRng.FormatConditions.Add(xlBlanksCondition)
   myCondition.StopIfTrue = True  ' ��ֵ������ʽ
   Dim i: For i = LBound(myBins) To UBound(myBins)
      
    Set myCondition = DataRng.FormatConditions.Add(Type:=xlCellValue, Operator:=xlEqual, Formula1:="=" & myBins(i))
    myCondition.Interior.Color = myColors(i)  ' ����Bin��Ӧ�������ɫ
    myCondition.Borders.LineStyle = xlContinuous  ' ��ӱ߿�
    Next
End Function

' ����ɫ�б�Χ�л�ȡ��ɫֵ
Private Function GetColorList(ColorListRng As Range) As Long()
   Dim Ret() As Long: ReDim Ret(1 To 7)
   With ColorListRng
      Dim i: For i = 1 To 7
         Ret(i) = .Cells(i, 1).Interior.Color  ' ��ȡ��Ԫ�񱳾�ɫ
      Next
   End With
   GetColorList = Ret
End Function

' Ϊ���ݷ�Χ����������ʽ��������ɫ�̶ȵ��б�
Public Function SetFormatCondtions(DataRng As Range, ColorScalPointList)
   Dim x: x = ColorScalPointList
   Dim ColorList() As Long: ColorList = GetColorList(DATA_COLOR_SHEET.Range("b2:b8"))
   
   Dim myCondition As FormatCondition: Set myCondition = DataRng.FormatConditions.Add(xlBlanksCondition)
   myCondition.StopIfTrue = True  ' ��ֵ������ʽ
   
   SetLimitCondtion DataRng, x(1), ColorList(7), False  ' С����Сֵ����ɫ
   SetBetweenCondtion DataRng, x(2), x(1), ColorList(6)  ' ������Сֵ�ʹ�Сֵ֮�����ɫ
   
   SetLimitCondtion DataRng, x(7), ColorList(2)  ' �������ֵ����ɫ
   SetBetweenCondtion DataRng, x(7), x(6), ColorList(1)  ' �������ֵ�ʹδ�ֵ֮�����ɫ
   
   SetColorScaleType DataRng, x(2), ColorList(5), x(4), ColorList(4), x(6), ColorList(3)  ' �м�ֵ����ɫ�̶�
   
End Function

' ������ɫ�̶�����������ʽ
Public Function SetColorScaleType(DataRng As Range, ParamArray p())
   'ParamArray p()����˳��,����ֵ,����ɫ
   Dim myType: myType = (UBound(p) + 1) / 2
   If myType > 3 And myType < 2 Then
      MsgBox "SetColorScaleType�������ݸ�������:" & UBound(p) + 1, vbInformation
   Else
      Dim myCondition As ColorScale
      Set myCondition = DataRng.FormatConditions.AddColorScale(myType)
      With myCondition
         Dim i: For i = LBound(p) To UBound(p) Step 2
            SetColorScaleCriterion .ColorScaleCriteria(i / 2 + 1), p(i), p(i + 1)  ' ����ÿ���̶ȵ�
         Next
      End With
   End If
End Function

' ������ɫ�̶�������׼
Private Function SetColorScaleCriterion(myColorScaleCriterion As ColorScaleCriterion, myVal, myColor)
   With myColorScaleCriterion
      .Type = xlConditionValueNumber  ' ʹ����ֵ����
      .Value = myVal  ' ���ÿ̶�ֵ
      .FormatColor.Color = myColor  ' ������ɫ
   End With
End Function

' ���ý�������ֵ֮���������ʽ
Private Function SetBetweenCondtion(DataRng As Range, HighVal, LowVal, DisplayColor)
   Dim myFormatCondition As FormatCondition
   Set myFormatCondition = DataRng.FormatConditions.Add(Type:=xlCellValue, Operator:=xlBetween, _
        Formula1:="=" & LowVal, Formula2:="=" & HighVal)
   myFormatCondition.Interior.Color = DisplayColor  ' �������ɫ
   myFormatCondition.StopIfTrue = True  ' �������Ϊ�棬ֹͣ������������
End Function

' ���ô���/С��ָ��ֵ��������ʽ
Private Function SetLimitCondtion(DataRng As Range, LimitVal, DisplayColor, Optional GreateFlag As Boolean = True)
   Dim myFormatCondition As FormatCondition
   Set myFormatCondition = DataRng.FormatConditions.Add(Type:=xlCellValue, _
        Operator:=IIf(GreateFlag, xlGreater, xlLess), _
        Formula1:="=" & LimitVal)
   myFormatCondition.Interior.Color = DisplayColor  ' �������ɫ
   myFormatCondition.StopIfTrue = True  ' �������Ϊ�棬ֹͣ������������
End Function

