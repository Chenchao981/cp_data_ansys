Attribute VB_Name = "������ֵ��ɫͼ"
Option Explicit

' --- ȫ�ֳ������� ---
' ��������� Excel �������ϵ� MAP ͼ�Ĵ��¸߶ȺͿ�� (��λ����?)
Public Const gMapHeight = 355 * 0.6
Public Const gMapWidth = 315 * 0.6

' ����ÿ����������ɫ�̶ȷֽ��
' TestVal: �������� Wafer ���в�������ֵ�� Range ���� (���� "Data" ������)
' ����ֵ: ��ά���� Ret(1 To 7, 1 To ParamCount)��ÿ�д洢һ�������� 7 ����ɫ�ֽ��
' �ֽ����㷽�������ķ�λ�� (Q1, Q2, Q3) ���ķ�λ�� (IQR = Q3 - Q1)
' 7 ����ͨ����Ӧ: Q1-3*IQR, Q1-1.5*IQR, Q1, Q2, Q3, Q3+1.5*IQR, Q3+3*IQR
Public Function ColorPointSetup(TestVal As Range)
   On Error Resume Next
   Dim x: x = TestVal.Value ' �� Range ���ݶ����������������
   If Err.Number <> 0 Or Not IsArray(x) Then Exit Function
   On Error GoTo 0
   
   Dim ParamCount As Long: ParamCount = UBound(x, 2)
   Dim Ret: ReDim Ret(1 To 7, 1 To ParamCount)
   Dim i As Long
   For i = 1 To ParamCount
      Dim myDataCol As Range: Set myDataCol = TestVal.Columns(i)
      
      On Error Resume Next ' ���� WorksheetFunction ���ܳ��ֵĴ��� (������Ϊ�ջ����ֵ)
      Dim Q1: Q1 = WorksheetFunction.Quartile_Inc(myDataCol, 1) ' ʹ�� Quartile_Inc (���� Excel 2010+)
      Dim Q2: Q2 = WorksheetFunction.Median(myDataCol)
      Dim Q3: Q3 = WorksheetFunction.Quartile_Inc(myDataCol, 3)
      Dim MaxVal: MaxVal = WorksheetFunction.Max(myDataCol)
      Dim MinVal: MinVal = WorksheetFunction.Min(myDataCol)
      If Err.Number <> 0 Then GoTo SkipParam ' �������ͳ���������������˲���
      On Error GoTo 0
      
      Dim IR As Double
      ' ��� Q1 �� Q3 �Ƿ���Ч�Ҳ�ͬ
      If IsNumeric(Q1) And IsNumeric(Q3) And Q1 <> Q3 Then
         IR = Q3 - Q1
         Ret(1, i) = Q1 - 3 * IR
         Ret(2, i) = Q1 - 1.5 * IR
         Ret(3, i) = Q1
         Ret(4, i) = Q2
         Ret(5, i) = Q3
         Ret(6, i) = Q3 + 1.5 * IR
         Ret(7, i) = Q3 + 3 * IR
         ' ��ѡ��������ֵ������ Min/Max ��Χ�� (��ǰ������ע�͵�)
         ' If Ret(1, i) < MinVal Then Ret(1, i) = MinVal
         ' If Ret(2, i) < MinVal Then Ret(2, i) = MinVal
         ' If Ret(6, i) > MaxVal Then Ret(6, i) = MaxVal
         ' If Ret(7, i) > MaxVal Then Ret(7, i) = MaxVal
      Else ' ��� Q1 = Q3 ����Ч����ʹ�� Min/Max �� Q1/Q3 �ļ�Ȩƽ�������岿�ֵ�
         Ret(1, i) = MinVal
         Ret(2, i) = IIf(IsNumeric(Q1), Q1 * 0.8 + MinVal * 0.2, MinVal) ' �����Բ�ֵ
         Ret(3, i) = Q1
         Ret(4, i) = Q2
         Ret(5, i) = Q3
         Ret(6, i) = IIf(IsNumeric(Q3), Q3 * 0.8 + MaxVal * 0.2, MaxVal)
         Ret(7, i) = MaxVal
      End If
SkipParam:
   Next i
   
   ColorPointSetup = Ret
End Function

' �������в�������ֵ��ɫͼ�� "ParamColorChart" ������������ɫ�̶���ӵ� PPT ��
Public Sub PlotDataColor(w As Workbook, myTestinfo As CPLot, myPPT As Object, myColorPoint)
   Dim PlotSheet As Worksheet: Set PlotSheet = w.Worksheets("ParamColorChart")
   Dim h As Long, WaferRowOffset As Long
   Dim WaferIndex As Long
   
   If Not IsArray(myColorPoint) Then
       gShow.ErrAlarm "��ɫ�ֽ��������Ч���޷����Ʋ�����ֵ��ɫͼ��"
       Exit Sub
   End If
   
   For WaferIndex = 1 To myTestinfo.WaferCount
      With myTestinfo.Wafers(WaferIndex)
         If .ChipCount = 0 Then GoTo NextWafer ' ����û�� Chip �� Wafer
         Dim MapGridWidth As Long: MapGridWidth = .Width + 2 ' ÿ�� Map �� Excel ��ռ�õĿ�� (����)
         Application.StatusBar = "���Ʋ�����ֵ��ɫͼ..." & .WaferId & "#"
         
         Dim j As Long: For j = 1 To myTestinfo.ParamCount
            ' ���㵱ǰ Map �� Excel �е���ʼ��Ԫ��
            Dim StartCell As Range: Set StartCell = PlotSheet.Range("b2").Offset(WaferRowOffset, MapGridWidth * (j - 1))
            StartCell.Offset(-1, -1) = .WaferId & "#" ' ��ע Wafer ID
            
            ' ��ȡ��ǰ��������ɫ�ֽ��
            Dim ParamColorPoint
            On Error Resume Next
            ParamColorPoint = WorksheetFunction.Index(myColorPoint, 0, j) ' �� myColorPoint ������ȡ�� j ��
            If Err.Number <> 0 Then GoTo SkipParamPlot ' �����ȡʧ�ܣ������˲���
            ParamColorPoint = WorksheetFunction.Transpose(ParamColorPoint) ' ת��Ϊһά����
            On Error GoTo 0
            
            ' ���� Map ����
            Dim myTitle As String
            myTitle = .WaferId & "#" & myTestinfo.Params(j).Id
            StartCell.Offset(-1, Int(MapGridWidth * 0.35)) = myTitle ' �� Map �Ϸ����¾�����ʾ����
            
            ' ���Ƶ�ǰ��������ɫ Map �� Excel������ӵ� PPT
            h = PlotParamColorChart(StartCell, myTestinfo.Wafers(WaferIndex), j, ParamColorPoint, myPPT) + 2 ' ��ȡ���Ƹ߶Ȳ��� 2 �м��
            
            ' ���ڴ����һ�� Wafer ʱ������ɫ�̶���ӵ���Ӧ�� PPT �����õ�Ƭ
            If WaferIndex = 1 Then AddScaleColor myPPT.slides(j + 2), ParamColorPoint
SkipParamPlot:
         Next j
         WaferRowOffset = WaferRowOffset + h ' ������һ�� Wafer Map ����ʼ��ƫ����
      End With
NextWafer:
   Next WaferIndex
   
   PlotSheet.Activate
   ActiveWindow.DisplayGridlines = False
  
End Sub

' ���Ƶ�����������ɫ Map �� Excel������ӵ� PPT
Private Function PlotParamColorChart(StartCell As Range, myWaferInfo As CPWafer, ParamIndex, ParamColorPoint, myPPT As Object) As Long
   Dim x, Y, ParamData
   ParamData = myWaferInfo.ChipDatas(ParamIndex) ' ��ȡ��ǰ����������
   x = myWaferInfo.x
   Y = myWaferInfo.Y
   
   ' ���������Ч��
   If Not IsArray(x) Or Not IsArray(Y) Or Not IsArray(ParamData) Then PlotParamColorChart = 0: Exit Function
   If UBound(x) <> UBound(Y) Or UBound(x) <> UBound(ParamData) Then PlotParamColorChart = 0: Exit Function
   If myWaferInfo.ChipCount = 0 Then PlotParamColorChart = 0: Exit Function
   
   On Error Resume Next
   Dim MinX: MinX = Application.WorksheetFunction.Min(x)
   Dim MaxX: MaxX = Application.WorksheetFunction.Max(x)
   Dim MinY: MinY = Application.WorksheetFunction.Min(Y)
   Dim MaxY: MaxY = Application.WorksheetFunction.Max(Y)
   If Err.Number <> 0 Then PlotParamColorChart = 0: Exit Function
   On Error GoTo 0
   
   ' ���� Excel Map ��Ԫ���С
   SetMapCellSize StartCell, MinY, MaxY, MinX, MaxX
   
   ' ������ά���� d ��������ֵ (X �ᷭת)
   Dim MapHeight As Long: MapHeight = MaxY - MinY
   Dim MapWidth As Long: MapWidth = MaxX - MinX
   Dim d: ReDim d(0 To MapHeight, 0 To MapWidth)
   Dim i As Long: For i = 1 To UBound(x)
      Dim xx As Integer: xx = x(i, 1) - MinX
      Dim yy As Integer: yy = Y(i, 1) - MinY
      If yy >= 0 And yy <= MapHeight And xx >= 0 And xx <= MapWidth Then
         d(yy, MaxX - x(i, 1)) = ParamData(i, 1)
      End If
   Next
   
   ' ������д�� Excel ��Ӧ��������ʽ
   Dim MapRng As Range: Set MapRng = StartCell.Resize(MapHeight + 1, MapWidth + 1)
   MapRng.Value = d
   SetFormatCondtions MapRng, ParamColorPoint ' Ӧ����ɫ�̶�������ʽ
   
   ' �� Excel Map ��ӵ���Ӧ�� PPT �����õ�Ƭ (�õ�Ƭ���� = �������� + 2)
   AddMap MapRng, myPPT.slides(2 + ParamIndex), CInt(myWaferInfo.WaferId)
   
   PlotParamColorChart = MapHeight + 1 ' ���ػ��Ƶ�����
End Function

' �� PPT �õ�Ƭ�������ɫ�̶�ͼ��
Private Function AddScaleColor(mySlide As Object, ParamColorPoint)
   On Error Resume Next
   ' 1. �� DATA_COLOR_SHEET ����Ԥ�������ɫ��ͼƬ ("Picture 1")
   DATA_COLOR_SHEET.Shapes("Picture 1").CopyPicture
   If Err.Number <> 0 Then
       gShow.ErrAlarm "�޷�������ɫ�̶�ͼƬ (���� DATA_COLOR_SHEET)��"
       Exit Function
   End If
   
   ' 2. ճ����ɫ��ͼƬ�� PPT �õ�Ƭ
   Dim myShape As Object: Set myShape = mySlide.Shapes.Paste
   If Err.Number <> 0 Or myShape Is Nothing Then
       gShow.ErrAlarm "�޷�ճ����ɫ�̶�ͼƬ���õ�Ƭ " & mySlide.SlideIndex & "��"
       Exit Function
   End If
   
   ' 3. ������ɫ����λ�� (���´�ֱ����)
   With myShape
      .Left = 40
      .Top = 40 + (500 - .Height) / 2 ' 500 �����ǻõ�Ƭ��������Ĺ��Ƹ߶�?
   End With
   
   ' 4. ����ɫ���Ա���ӱ�ʾ����ֵ��ɫ��С���� (��ɫ���� DATA_COLOR_SHEET)
   ' (��Щ���ε���ɫ��λ���ƺ���Ӳ����ģ���Ӧ��ɫ�̶ȵ����˶�����ɫ)
   Dim RectShape As Object
   Set RectShape = mySlide.Shapes.AddShape(msoShapeRectangle, 40, myShape.Top - 20, 10, 15)
   If Not RectShape Is Nothing Then
       RectShape.Fill.ForeColor.RGB = DATA_COLOR_SHEET.Range("b3").Interior.Color
       RectShape.Line.Visible = False
   End If
   Set RectShape = mySlide.Shapes.AddShape(msoShapeRectangle, 40, myShape.Top - 40, 10, 15)
   If Not RectShape Is Nothing Then
       RectShape.Fill.ForeColor.RGB = DATA_COLOR_SHEET.Range("b2").Interior.Color
       RectShape.Line.Visible = False
   End If
   Set RectShape = mySlide.Shapes.AddShape(msoShapeRectangle, 40, myShape.Top + myShape.Height + 5, 10, 15)
   If Not RectShape Is Nothing Then
       RectShape.Fill.ForeColor.RGB = DATA_COLOR_SHEET.Range("b7").Interior.Color
       RectShape.Line.Visible = False
   End If
   Set RectShape = mySlide.Shapes.AddShape(msoShapeRectangle, 40, myShape.Top + myShape.Height + 25, 10, 15)
   If Not RectShape Is Nothing Then
       RectShape.Fill.ForeColor.RGB = DATA_COLOR_SHEET.Range("b8").Interior.Color
       RectShape.Line.Visible = False
   End If
   
   ' 5. ����ɫ���;����Ա������ֵ��ǩ (��ʾ��Ӧ����ɫ�ֽ��ֵ)
   AddScaleLabel mySlide, myShape.Top - 20, ParamColorPoint(7) ' ��Ӧ b3 ��ɫ (Q3+3IQR)
   AddScaleLabel mySlide, myShape.Top, ParamColorPoint(6)      ' ��ɫ������ (Q3+1.5IQR)
   AddScaleLabel mySlide, myShape.Top + myShape.Height / 2, ParamColorPoint(4) ' ��ɫ���м� (Q2)
   AddScaleLabel mySlide, myShape.Top + myShape.Height, ParamColorPoint(2) ' ��ɫ���׶� (Q1-1.5IQR)
   AddScaleLabel mySlide, myShape.Top + myShape.Height + 20, ParamColorPoint(1) ' ��Ӧ b7 ��ɫ (Q1-3IQR)
   ' ע�⣺�����ǩ��Ӧ�� ParamColorPoint ��������ɫ���õ��߼�������Ҫ��ϸ�˶�
   On Error GoTo 0
End Function

' �� PPT �õ�Ƭָ����ֱλ�� (Top) �����ֵ��ǩ
Private Function AddScaleLabel(mySlide As Object, Top As Single, info As Variant)
   If IsEmpty(info) Or Not IsNumeric(info) Then Exit Function ' ���ֵ��Ч����ӱ�ǩ
   On Error Resume Next
   With mySlide.Shapes.AddLabel(msoTextOrientationHorizontal, 1, Top - 10, 80, 50)
      ' ��ʽ����ֵ��ʾ (ʹ�� ChangeDisplayNum ����)
      .TextFrame.TextRange.Text = Right(Space(6) & ChangeDisplayNum(info), 6) & "->"
      .Line.Visible = False
      .TextEffect.FontSize = 10
   End With
   On Error GoTo 0
End Function

' ����ֵת��Ϊ����λ��׺ (m, u, n, p) ���ַ�����������λ��
Private Function ChangeDisplayNum(info) As String
   If IsEmpty(info) Or Not IsNumeric(info) Then ChangeDisplayNum = "": Exit Function
   Dim Ret As String
   Dim AbsVal: AbsVal = Abs(CDbl(info))
   
   Select Case AbsVal
   Case 0: Ret = "0"
   Case Is >= 1: Ret = SetNumberQty(info)
   Case Is >= 0.001: Ret = SetNumberQty(Round(info * 1000, 3)) & "m"
   Case Is >= 0.000001: Ret = SetNumberQty(Round(info * 1000000#, 3)) & "u"
   Case Is >= 0.000000001: Ret = SetNumberQty(Round(info * 1000000000#, 3)) & "n"
   Case Is > 0: Ret = SetNumberQty(Round(info * 1000000000000#, 3)) & "p"
   Case Else: Ret = SetNumberQty(info) ' ��������δ���ǵ����
   End Select
   ChangeDisplayNum = Ret
End Function

' ��ʽ�������ַ�����������λ�����ƺ��ǰ���С�����С�����ֵĹ̶�λ����ʽ?��
Public Function SetNumberQty(info) As String
   Const N As Integer = 4 ' Ŀ����λ��?
   Dim Ret As String
   Ret = CStr(info)
   
   ' ����С���㿪ͷ������
   If Left(Ret, 1) = "." Then
      Ret = "0" & Left(Ret, N) ' ����С����� N-1 λ?
   ' ��������С���㿪ͷ
   ElseIf Left(Ret, 2) = "-." Then
      Ret = "-0." & Mid(Ret, 3, N - 2) ' ����С����� N-2 λ?
   Else
      Dim Pos As Integer: Pos = InStr(Ret, ".")
      If Pos > 0 Then ' �����С����
         ' ������������λ������С��λ����ʹ������Ч���֣����ܳ��ȣ����ӽ� N
         Dim DecimalPlaces As Integer: DecimalPlaces = N - Pos + IIf(Left(Ret, 1) = "-", 0, 1) ' ���㱣����С��λ��
         If DecimalPlaces < 0 Then DecimalPlaces = 0
         Ret = CStr(Round(info, DecimalPlaces))
      'Else ' �����������������Ҫ���Ƴ��Ȼ��㣬��ǰ����δ����
      End If
   End If
   SetNumberQty = Ret
End Function

' (�˺����ƺ�δ������)
' ����һ����Ԫ�� Interior ����Ķ�ά���� (��;����)
Private Function CreateCellArray(x, Y, MinX As Integer, MinY As Integer, StartCell As Range, Result() As Interior)
   With StartCell
      Dim i As Long: For i = 1 To UBound(x)
         Dim xx As Integer: xx = x(i, 1) - MinX
         Dim yy As Integer: yy = Y(i, 1) - MinY
         If yy >= LBound(Result, 1) And yy <= UBound(Result, 1) And xx >= LBound(Result, 2) And xx <= UBound(Result, 2) Then
             Set Result(yy, xx) = .Offset(yy, xx).Interior
         End If
      Next
   End With
End Function

' �ظ����壺���� Excel Map ��Ԫ���С (�� ����MAPͼ.bas �еĺ����ظ�)
Private Sub SetMapCellSize(StartCell As Range, Min_Py, Max_Py, Min_Px, Max_Px)
   Dim MapCellHeight As Double, MapCellWidth As Double
   Dim HeightFactor As Long: HeightFactor = Max_Py - Min_Py + 1
   Dim WidthFactor As Long: WidthFactor = Max_Px - Min_Px + 1
   
   If HeightFactor <= 0 Or WidthFactor <= 0 Then Exit Sub
   
   MapCellHeight = gMapHeight / HeightFactor
   MapCellWidth = 0.125 * gMapWidth / WidthFactor
   
   If MapCellHeight <= 0 Then MapCellHeight = 1
   If MapCellWidth <= 0 Then MapCellWidth = 1
   
   On Error Resume Next
   With StartCell.Resize(HeightFactor, WidthFactor)
      .ColumnWidth = MapCellWidth
      .RowHeight = MapCellHeight
   End With
   On Error GoTo 0
End Sub
   
' �� Excel �� Long ������ɫֵת��Ϊ RGB ����
Public Function CLng2RGB(x As Long)
   Dim R As Long, G As Long, B As Long
   R = x Mod 256
   G = (x \ 256) Mod 256
   B = (x \ 65536) Mod 256
   CLng2RGB = Array(R, G, B)
End Function
