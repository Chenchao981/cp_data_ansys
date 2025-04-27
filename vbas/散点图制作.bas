Attribute VB_Name = "ɢ��ͼ����"
Option Explicit

' �����û��Զ������������õĽṹ
Type UserCoordinateSetup
   TestItem As String        ' �������Ӧ�Ĳ�����Ŀ���� (���� Params().Id)
   SetupMethod As String     ' ������̶����÷��� ("�Զ�" �� "�ֹ�ָ��")
   MinimumScale As Variant   ' �ֹ�ָ������С�̶�
   MaximumScale As Variant   ' �ֹ�ָ�������̶�
   AxisTitle As String       ' �Զ������������� (���Ϊ�գ���ʹ�� TestItem)
End Type

' ���嵥��ɢ��ͼ������������Ϣ
Type ScatterPlotChartSetup
   Title As String             ' ͼ����� (�û��Զ��岿��)
   XAxis As UserCoordinateSetup ' X ������
   YAxis As UserCoordinateSetup ' Y ������
   WaferCount As Integer       ' ��ͼ�����ö�Ӧ�� Wafer ���� (ͨ������ Lot �е� Wafer ����)
   WaferCode() As String       ' Wafer ����б� (���� TestInfo.Wafers(i).WaferId)
   ValueRng() As Range         ' Y ������Դ Range �������� (ÿ��Ԫ�ض�Ӧһ�� Wafer �� Y ������)
   XValueRng() As Range        ' X ������Դ Range �������� (ÿ��Ԫ�ض�Ӧһ�� Wafer �� X ������)
End Type

' ����ɢ��ͼ������Ϣ������ģ��ͼ�����Ͷ��ͼ������
Type ScatterPlotSample
   SampleChartObject As ChartObject    ' ��Ϊģ���ͼ����� (���� XY_SETUP_SHEET)
   ChartCount As Integer             ' ��Ҫ���ɵ�ͼ������ (���� XY_SETUP_SHEET ��������������)
   ChartSetup() As ScatterPlotChartSetup ' �洢ÿ��ͼ�����õ�����
End Type

' ������������������������ɢ��ͼ
Public Function PlotScatterChart(ResultBook As Workbook, _
                                 SampleSheet As Worksheet, _
                                 myTestinfo As CPLot)
   With ResultBook
      Dim d As Worksheet: Set d = .Worksheets("Data") ' ����Դ������
      Dim s As Worksheet: Set s = .Worksheets("Scatter") ' Ŀ��ͼ������
   End With
   Dim mySample As ScatterPlotSample
   ' 1. ��ȡģ������ã�����������Դ
   mySample = CreateScatterPlotSample(d, SampleSheet, myTestinfo)
   ' 2. ���ݶ�ȡ�������ú����ݣ��������ͼ��
   PlotBySample mySample, s
End Function

' ������������ (mySample) ѭ����������ͼ��Ŀ�깤���� (PlotSheet)
Private Function PlotBySample(mySample As ScatterPlotSample, PlotSheet As Worksheet)
   With mySample
      ' ����ÿ��ͼ������ (ChartSetup)
      Dim ChartIndex: For ChartIndex = 1 To .ChartCount
         ' ���������ö�Ӧ��ÿ�� Wafer
         Dim Wafer: For Wafer = 1 To .ChartSetup(ChartIndex).WaferCount
            ' Ϊ��ǰ ChartIndex �� WaferIndex ����һ���µ�ͼ��
            CreateNewChart mySample, PlotSheet, ChartIndex, Wafer
         Next
      Next
   End With
End Function

' ���������µ�ɢ��ͼ
Public Function CreateNewChart(mySample As ScatterPlotSample, _
                               PlotSheet As Worksheet, _
                               ChartIndex, WaferIndex)
   
   Dim Title As String
   Dim XAxis As UserCoordinateSetup
   Dim YAxis As UserCoordinateSetup
   Dim Xvalues As Range
   Dim Yvalues As Range
   
   ' �� mySample ����ȡ��ǰͼ���������Ϣ
   With mySample
      With .ChartSetup(ChartIndex)
         ' ����ͼ�����: WaferID# + (�û��Զ������ �� X-Y��Ŀ��) + " Chart"
         Title = .WaferCode(WaferIndex) & "# "
         Title = Title & FirstVaildContent(.Title, .XAxis.TestItem & "-" & .YAxis.TestItem)
         Title = Title & " Chart"
         ' ��ȡ X, Y �����ú�����Դ
         XAxis = .XAxis
         YAxis = .YAxis
         Set Xvalues = .XValueRng(WaferIndex)
         Set Yvalues = .ValueRng(WaferIndex)
      End With
      ' ����ģ��ͼ��
      .SampleChartObject.Copy
   End With
   
   ' ��Ŀ�깤����ճ����������ͼ��
   With PlotSheet
      .Paste
      With .ChartObjects(.ChartObjects.Count) ' �����ո�ճ����ͼ�����
         ' ����ͼ��λ�� (�� ChartIndex ˮƽ���У��� WaferIndex ��ֱ����)
         .Left = 10 + (ChartIndex - 1) * (20 + .Width)
         .Top = 10 + (WaferIndex - 1) * (.Height + 20)
         With .Chart
            ' ���� X, Y ������Ŀ̶Ⱥͱ���
            UpdateAxis .Axes(xlCategory), XAxis ' X ��
            UpdateAxis .Axes(xlValue), YAxis    ' Y ��
            .HasTitle = True
            .ChartTitle.Text = Title ' ����ͼ�����
            ' ��������ϵ�е�����Դ
            If .SeriesCollection.Count > 0 Then ' ȷ��ģ��ͼ��������ϵ��
               With .SeriesCollection(1)
                  .Name = "x-y" ' ϵ������
                  .Xvalues = Xvalues ' X ������
                  .Values = Yvalues  ' Y ������
               End With
            Else
               ' ���ģ��û��ϵ�У����Կ������һ���µ�
               ' Dim sc As Series: Set sc = .SeriesCollection.NewSeries
               ' sc.ChartType = xlXYScatter
               ' sc.Name = "x-y"
               ' sc.Xvalues = Xvalues
               ' sc.Values = Yvalues
            End If
         End With
      End With
   End With
End Function

' ��������������� (�̶ȡ�����)
Private Function UpdateAxis(myAxis As Axis, _
                            myAxisSetup As UserCoordinateSetup)
   With myAxisSetup
      ' �������Ϊ�ֹ�ָ���̶�
      If .SetupMethod = "�ֹ�ָ��" Then
         If Not IsEmpty(.MinimumScale) And IsNumeric(.MinimumScale) Then
            myAxis.MinimumScale = .MinimumScale
            myAxis.MinimumScaleIsAuto = False
         Else
            myAxis.MinimumScaleIsAuto = True
         End If
         If Not IsEmpty(.MaximumScale) And IsNumeric(.MaximumScale) Then
            myAxis.MaximumScale = .MaximumScale
            myAxis.MaximumScaleIsAuto = False
         Else
            myAxis.MaximumScaleIsAuto = True
         End If
      Else ' ������Զ��̶�
            myAxis.MinimumScaleIsAuto = True
            myAxis.MaximumScaleIsAuto = True
      End If
      ' ������������� (����ʹ���Զ�����⣬����ʹ�ò�����Ŀ����)
      myAxis.HasTitle = True
      myAxis.AxisTitle.Text = FirstVaildContent(.AxisTitle, .TestItem)
   End With
End Function

' ���� ScatterPlotSample �ṹ������ģ��ͼ������ͼ�����ã�����������Դ
Private Function CreateScatterPlotSample(DataSheet As Worksheet, _
                                         ChartSampleSheet As Worksheet, _
                                         myTestinfo As CPLot) As ScatterPlotSample
   Dim Ret As ScatterPlotSample
   ' 1. ��ȡģ��ͼ����� (������ ChartSampleSheet �ĵ�һ�� ChartObject)
   Set Ret.SampleChartObject = ChartSampleSheet.ChartObjects(1)
   ' 2. �� ChartSampleSheet ��ȡ�û������ͼ������ (X/Y����Ŀ���̶ȡ������)
   AddSetupInfo ChartSampleSheet, Ret
   ' 3. �������ã��� DataSheet ����ÿ��ͼ����������� X/Y ����Դ Range
   AddWaferData Ret, DataSheet, myTestinfo
   CreateScatterPlotSample = Ret
End Function

' ��ɢ��ͼ���ù����� (ChartSampleSheet) ��ȡ�û������ͼ��������Ϣ
Private Function AddSetupInfo(ChartSampleSheet As Worksheet, Ret As ScatterPlotSample)
   Dim ContentArray
   On Error Resume Next
   ContentArray = ChartSampleSheet.Range("a1").CurrentRegion.Value
   If Err.Number <> 0 Or Not IsArray(ContentArray) Then Exit Function ' ��ȡʧ�ܻ�����Ϊ�����˳�
   On Error GoTo 0
   
   If UBound(ContentArray, 2) < 2 Then Exit Function ' ������Ҫ���� (������ + һ������)
   
   Dim ColIndex As Integer: For ColIndex = 2 To UBound(ContentArray, 2)
      ' ��� X ��� Y ��Ĳ�����Ŀ�����Ƿ�����д (��5�к͵�11��)
      If ContentArray(5, ColIndex) <> "" And ContentArray(11, ColIndex) <> "" Then
         With Ret
            .ChartCount = .ChartCount + 1
            ReDim Preserve .ChartSetup(1 To .ChartCount)
            With .ChartSetup(.ChartCount)
               .Title = ContentArray(3, ColIndex) ' ͼ����� (�û�����)
               .XAxis = CreateNewUserCoordinateSetup(ContentArray, ColIndex, 4) ' ��ȡ X ������
               .YAxis = CreateNewUserCoordinateSetup(ContentArray, ColIndex, 10) ' ��ȡ Y ������
            End With
         End With
      End If
   Next
End Function

' ���ݴ����ñ��ȡ����������������������� UserCoordinateSetup �ṹ
Private Function CreateNewUserCoordinateSetup(ContentArray, _
                                              ColIndex As Integer, _
                                              StartRow As Long) As UserCoordinateSetup
   Dim Ret As UserCoordinateSetup
   With Ret
      .TestItem = ContentArray(StartRow + 1, ColIndex)    ' ������Ŀ����
      .SetupMethod = ContentArray(StartRow + 2, ColIndex) ' �̶����÷���
      If .SetupMethod = "�ֹ�ָ��" Then
         .MinimumScale = ContentArray(StartRow + 3, ColIndex) ' ��С�̶�
         .MaximumScale = ContentArray(StartRow + 4, ColIndex) ' ���̶�
      End If
      .AxisTitle = ContentArray(StartRow + 5, ColIndex)    ' ���������
   End With
   CreateNewUserCoordinateSetup = Ret
End Function

' Ϊ ScatterPlotSample �е�ÿ��ͼ�����ù���ʵ�ʵ�����Դ Range
Private Function AddWaferData(mySample As ScatterPlotSample, _
                              DataSheet As Worksheet, _
                              myTestinfo As CPLot)
   ' 1. ���� Wafer ��Ϣ���� (���� WaferCode ��ÿ�� Wafer �����������ʼ����Ϣ)
   Dim WaferRowInfo: WaferRowInfo = CreateWaferInfo(myTestinfo, DataSheet)
   ' 2. ����������Ŀ���Ƶ� DataSheet ��������ӳ���ֵ�
   Dim TestItemColDic As Object: Set TestItemColDic = CreateTestItemColDic(myTestinfo)
   
   With mySample
      Dim ChartIndex As Integer: For ChartIndex = 1 To .ChartCount
         With .ChartSetup(ChartIndex)
            .WaferCount = myTestinfo.WaferCount
            .WaferCode = WaferRowInfo(1) ' ���� Wafer ����б�
            ' ���� X/Y �����õ� TestItem ���ƣ����Ҷ�Ӧ��������������ȡÿ�� Wafer ������ Range
            .XValueRng = GetPlotDataRng(.XAxis.TestItem, WaferRowInfo(2), TestItemColDic)
            .ValueRng = GetPlotDataRng(.YAxis.TestItem, WaferRowInfo(2), TestItemColDic)
         End With
      Next
   End With
End Function

' ����һ������ WaferCode �б��ÿ�� Wafer �� DataSheet �����ݷ�Χ������
' ����ֵ: һ����ά���� Ret(1 to 2)
' Ret(1): �������� WaferId ��һά����
' Ret(2): ����ÿ�� Wafer �������� (A��) �� Range �����һά����
Private Function CreateWaferInfo(myTestinfo As CPLot, DataSheet As Worksheet)
   Dim Ret: ReDim Ret(1 To 2)
   With myTestinfo
      If .WaferCount = 0 Then Exit Function
      Dim WaferRng() As Range: ReDim WaferRng(1 To .WaferCount)
      Dim WaferCode() As String: ReDim WaferCode(1 To .WaferCount)
      Dim StartRow As Long: StartRow = 2 ' ���ݴӵ� 2 �п�ʼ
      Dim i: For i = 1 To .WaferCount
         With .Wafers(i)
           Dim DataRows As Long: DataRows = .ChipCount
           WaferCode(i) = .WaferId
           Set WaferRng(i) = DataSheet.Cells(StartRow, 1).Resize(DataRows) ' ��ȡ A �е����ݷ�Χ
           StartRow = StartRow + DataRows ' ������һ�� Wafer ����ʼ��
         End With
      Next
   End With
   Ret(1) = WaferCode
   Ret(2) = WaferRng
   CreateWaferInfo = Ret
End Function

' ����һ���Ӳ�����Ŀ���� (TestItem.Id) ������ DataSheet �ж�Ӧ�кŵ�ӳ���ֵ�
Private Function CreateTestItemColDic(myTestinfo As CPLot) As Object
   Dim Ret As Object: Set Ret = CreateObject("scripting.dictionary")
   Ret.CompareMode = vbTextCompare ' �����ֵ��ֵ�Ƚ�Ϊ�����ִ�Сд
   Dim DataStartCol As Long: DataStartCol = 6 ' �����дӵ� 6 �� (F��) ��ʼ
   With myTestinfo
      Dim i: For i = 1 To .ParamCount
         With .Params(i)
            Dim TestItemName As String: TestItemName = .Id
            ' ������ܵ�������� (��Ȼ CPLot �ṹ�� Id Ӧ����Ψһ��)
            Dim k As Integer: k = 1
            Do While Ret.exists(TestItemName)
               k = k + 1
               TestItemName = .Id & k
            Loop
            Ret.Add TestItemName, i + DataStartCol - 1 ' �洢 ItemName -> �к� ��ӳ��
         End With
      Next
   End With
   Set CreateTestItemColDic = Ret
End Function

' ���ݲ�����Ŀ���� (TestItem) ��ӳ���ֵ��л�ȡ�кţ�������ÿ�� Wafer ��Ӧ�е����� Range ����
Private Function GetPlotDataRng(TestItem As String, WaferRngs, TestItemColDic As Object)
   Dim DataCol As Variant
   DataCol = TestItemColDic(TestItem) ' ���ֵ��ȡ�к�
   If IsEmpty(DataCol) Then
       gShow.ErrStop "ɢ��ͼ���ô���", OCAP:="������Ŀ���� '" & TestItem & "' �����ݱ���δ�ҵ���Ӧ���С�"
       End ' ��ֹ��
   End If
   GetPlotDataRng = WaferRngOffset(WaferRngs, CInt(DataCol))
End Function

' ���� Wafer �� A �� Range ���� (WaferRngList) ��Ŀ���к� (TestItemCol)������ÿ�� Wafer ��ӦĿ���е����� Range ����
Private Function WaferRngOffset(WaferRngList, TestItemCol As Integer) As Range()
   Dim Ret() As Range
   If Not IsArray(WaferRngList) Then Exit Function
   ReDim Ret(LBound(WaferRngList) To UBound(WaferRngList))
   Dim i: For i = LBound(WaferRngList) To UBound(WaferRngList)
      Set Ret(i) = WaferRngList(i).Offset(0, TestItemCol - 1) ' A ���ǵ� 1 �У�����ƫ������ Col - 1
   Next
   WaferRngOffset = Ret
End Function

' �ӿɱ���������з��ص�һ���ǿ��ַ���
Public Function FirstVaildContent(ParamArray argv()) As String
   Dim Ret As String
   Dim s: For Each s In argv
      If Not IsEmpty(s) And Len(Trim(CStr(s))) > 0 Then
         Ret = Trim(CStr(s))
         Exit For
      End If
   Next
   FirstVaildContent = Ret
End Function

' ���ɢ��ͼ���� (XY_SETUP_SHEET) �Ƿ���Ч
Public Function SetupCheck_SCATTER_PLOT(TestInfo As CPLot) As Boolean
   Dim SetupOk As Boolean: SetupOk = True ' Ĭ������Ϊ True
   Dim TestItemColDic As Object: Set TestItemColDic = CreateTestItemColDic(TestInfo)
   Dim ContentArray
   
   On Error Resume Next
   ContentArray = XY_SETUP_SHEET.Range("a1").CurrentRegion.Value
   If Err.Number <> 0 Or Not IsArray(ContentArray) Then
       gShow.ErrAlarm "�޷���ȡɢ��ͼ���ñ� (XY_SETUP_SHEET) �����ݡ�"
       SetupCheck_SCATTER_PLOT = False
       Exit Function
   End If
   On Error GoTo 0
   
   If UBound(ContentArray, 2) < 2 Then SetupCheck_SCATTER_PLOT = True: Exit Function ' û�������У���Ϊ OK
   
   Dim ColIndex As Integer: For ColIndex = 2 To UBound(ContentArray, 2)
      ' ��� X �� (��5��) �� Y �� (��11��) �� TestItem �Ƿ�����д
      Dim XItem: XItem = ContentArray(5, ColIndex)
      Dim YItem: YItem = ContentArray(11, ColIndex)
      If XItem <> "" And YItem <> "" Then
         ' ��� X ��� Y ��� TestItem �Ƿ����������д���
         If TestItemColDic.exists(XItem) = False Then
            gShow.ErrAlarm Array("�����XYɢ��ͼ����", _
                                 "ͼ " & ColIndex - 1, _
                                 "X����Ŀ [" & XItem & "] ���Ʋ����ڻ��������в�ƥ�䡣")
            SetupOk = False
         End If
         If TestItemColDic.exists(YItem) = False Then
            gShow.ErrAlarm Array("�����XYɢ��ͼ����", _
                                 "ͼ " & ColIndex - 1, _
                                 "Y����Ŀ [" & YItem & "] ���Ʋ����ڻ��������в�ƥ�䡣")
            SetupOk = False
         End If
      End If
   Next
   SetupCheck_SCATTER_PLOT = SetupOk
End Function

