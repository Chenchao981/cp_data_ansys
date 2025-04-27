Attribute VB_Name = "A_ҵ������"
Option Explicit

' �����������б������ö��ŷָ�
Const SHEET_NAME_LIST As String = "Spec,Data,Yield,Summary,Map,BoxPlot,Scatter,ParamColorChart"

' ȫ�ֶ���ʵ��
Public gShow As New clsShowInfo  ' ��Ϣ��ʾ��ʵ��
Public RegEx As New clsRegEx     ' ������ʽ��ʵ��

Dim ToolTimer                    ' �������м�ʱ��
Dim BookSaved As Boolean         ' �������Ƿ��ѱ����־

' ����CP���ݸ�ʽ��ȡ�ļ��б�
Private Function GetFileList(CPDataFormat As String)
   Dim Ret
   Select Case CPDataFormat
   Case "MEX"
      Ret = PickupFile("��������", True, "xls")        ' MEX��ʽ��ѡ��xls�ļ����ɶ�ѡ
   Case "DCP"
      Ret = PickupFile("��������", True, "txt")        ' DCP��ʽ��ѡ��txt�ļ����ɶ�ѡ
   Case "CWSW"
      Ret = PickupFile("��������", True, "csv")        ' CW����Բ��ʽ��ѡ��csv�ļ����ɶ�ѡ
   Case "CWMW"
      Ret = PickupFile("��������", False, "csv")       ' CW�ྦྷԲ��ʽ��ѡ��csv�ļ�����ѡ
   Case Else
   '
   End Select
   GetFileList = Ret
End Function

' ���������������
Sub main()
   InitSheetSetup                                            ' ��ʼ������������
   Dim CPDataFormat As String: CPDataFormat = GetCPDataFormat()  ' ��ȡCP���ݸ�ʽ
   
   Dim fList: fList = GetFileList(CPDataFormat): If IsEmpty(fList) Then Exit Sub  ' ��ȡ�ļ��б����Ϊ�����˳�
   
   StartMarco                                                ' ��ʼ�괦��
   
   Dim TestInfo As CPLot: TestInfo = ReadFile(fList, CPDataFormat)  ' ��ȡ�ļ�����
   If TestInfo.WaferCount = 0 Then Exit Sub                  ' ���û�о�Բ�������˳�
   If SetupCheck(TestInfo) = False Then gShow.ErrStop "���ô��ڴ���", OCAP:="���������ú�����"  ' ������ã��д�������ֹ
   
   If ADD_CAL_DATA_FLAG Then AddCalData TestInfo            ' �����Ҫ����Ӽ�������
   
   Dim ResultBook As Workbook: Set ResultBook = CreateResultBook(SHEET_NAME_LIST)  ' �������������
   FillSpec ResultBook, TestInfo                            ' ���������
   FillTestData ResultBook, TestInfo                        ' ����������
   ShowYield ResultBook, TestInfo                           ' ��ʾ��������
   mySummary ResultBook, TestInfo                           ' ��������ժҪ
'
   If BOX_PLOT_FLAG Then
      PlotAllParamBoxChart ResultBook, TestInfo, CheckFactWaferQty(TestInfo)  ' �����Ҫ����������ͼ
   End If
   
   Dim myPPT As Object
   If BIN_MAP_PLOT_FLAG Then
      If myPPT Is Nothing Then Set myPPT = CreateResultPPT(TestInfo)  ' �������PPT����
      PlotAllMap ResultBook, TestInfo, myPPT                ' ��������Binͼ
   End If
'
   If DATA_COLOR_PLOT_FLAG Then
      Dim myColorPoint
      myColorPoint = ColorPointSetup(GetAllTestVal(ResultBook.Worksheets("Data")))  ' ������ɫ��
      If myPPT Is Nothing Then Set myPPT = CreateResultPPT(TestInfo)  ' �������PPT����
      PlotDataColor ResultBook, TestInfo, myPPT, myColorPoint  ' ����������ɫͼ
   End If
'
   If SCATTER_PLOT_FLAG Then PlotScatterChart ResultBook, XY_SETUP_SHEET, TestInfo  ' �����Ҫ������ɢ��ͼ
'
   Dim myReusltFileName As String: myReusltFileName = SaveResultBook(ResultBook, TestInfo.Product)  ' ������������
   If Not myPPT Is Nothing Then myPPT.Save                  ' ���PPT���ڣ��򱣴�PPT
   
   FinishMarco                                              ' ��ɺ괦��
   
End Sub

' ��ʼ�괦������״̬�ͼ�ʱ
Private Sub StartMarco()
   ToolTimer = Timer                            ' ��¼��ʼʱ��
   BookSaved = ThisWorkbook.Saved               ' ���浱ǰ������״̬
   'ShowPrompt
   Application.ScreenUpdating = False           ' �ر���Ļ����
   Application.Calculation = xlCalculationManual ' �����ֶ�����
End Sub

' ��ɺ괦���ָ�״̬����ʾ�����Ϣ
Private Sub FinishMarco()
   Application.Calculation = xlCalculationAutomatic ' �ָ��Զ�����
   Application.StatusBar = False                   ' ���״̬��
   ThisWorkbook.Saved = BookSaved                  ' �ָ�����������״̬
   UI_SHEET.Activate                               ' ����UI������
   MsgBox "finish" & vbLf & "time(s):" & _
      Format(Timer - ToolTimer, "0.0"), vbInformation + vbOKOnly  ' ��ʾ�����Ϣ�ͺ�ʱ
End Sub

' �����������Ƿ���ȷ
Private Function SetupCheck(TestInfo As CPLot) As Boolean
   Dim Ret As Boolean: Ret = True
   
   If ADD_CAL_DATA_FLAG Then
      If False = SetupCheck_ADD_CAL_DATA(TestInfo) Then Ret = False  ' ��������������
   End If
   
   If BOX_PLOT_FLAG And INCLUDE_EXP_FACT_FLAG Then
      If False = CheckFactWaferQty(TestInfo) Then Ret = False        ' ���ʵ����������
   End If
   
   If SCATTER_PLOT_FLAG Then
      If False = SetupCheck_SCATTER_PLOT(TestInfo) Then Ret = False  ' ���ɢ��ͼ����
   End If
   
   SetupCheck = Ret
End Function


' ��������������ָ��λ��
Private Function SaveResultBook(Result As Workbook, Lot) As String
   Dim mySaveFileName As String
   Dim myPath As String
   myPath = ThisWorkbook.Path & "\�����������ļ�\"      ' ���ñ���·��
   If Dir(myPath, vbDirectory) = "" Then MkDir myPath    ' ���·���������򴴽�
   mySaveFileName = myPath & Lot & ".xlsx"               ' �����ļ���
   If Dir(mySaveFileName) <> "" Then Kill mySaveFileName ' ����ļ��Ѵ�����ɾ��
   Result.SaveAs mySaveFileName                          ' ���湤����
   SaveResultBook = mySaveFileName
End Function

' ��ʾ������ʾ��Ϣ
Private Sub ShowPrompt()
   Dim info() As String: ReDim info(1 To 6)
   info(1) = "˵��"
   info(2) = "-------------------------------------------------"
   info(3) = "���Ȼᵯ���ļ�ѡ���,"
   info(4) = "��ָ����Ҫ�����csv�����ļ�"
   info(5) = "Ȼ�󹤾߻Ὣcsv�ļ���ʽת��"
   info(6) = "���������Ϊxlsx�ļ�"
   MsgBox Join(info, vbCrLf), vbOKOnly, "��ʾ"          ' ��ʾ����˵��
End Sub

' ��ȡ�ļ�����
Private Function ReadFile(fList, CPDataFormat As String) As CPLot
   Dim Ret As CPLot
   Dim DataBooks() As Workbook
   If CPDataFormat = "DCP" Then
      DataBooks = OpendBooks(fList, "OpenTabTextxlDelimitedFile")  ' DCP��ʽʹ������Ĵ򿪷�ʽ
   Else
      DataBooks = OpendBooks(fList)                                ' ������ʽ��׼��
   End If
       
   Dim WaferDataSheets() As Worksheet
   WaferDataSheets = GetWaferDataSheets(DataBooks)                ' ��ȡ��Բ���ݹ�����
   If CPDataFormat = "CWMW" Then
      Ret.PassBin = 1
      SplitInfo_CWMW Ret, WaferDataSheets(1)                     ' CW�ྦྷԲ��ʽ����
   Else
      With Ret
         .WaferCount = UBound(WaferDataSheets) - LBound(WaferDataSheets) + 1  ' ���þ�Բ����
         ReDim .Wafers(1 To .WaferCount)
         Dim i: For i = LBound(WaferDataSheets) To UBound(WaferDataSheets)
            Select Case CPDataFormat
            Case "CWSW"
               .PassBin = 1
               SplitInfo_CWSW Ret, WaferDataSheets(i), i         ' CW����Բ��ʽ����
            Case "MEX"
               .PassBin = 1
               SplitInfo_MEX Ret, WaferDataSheets(i), i          ' MEX��ʽ����
            Case "DCP"
               .PassBin = 1
               SplitInfo_DCP Ret, WaferDataSheets(i), i          ' DCP��ʽ����
            Case Else
               MsgBox "δ����ĸ�ʽ", vbCritical, "��ֹ����"     ' δ֪��ʽ����
               Exit For
            End Select
         Next
      End With
   End If
   CloseBooks DataBooks                                          ' �ر����ݹ�����
   ReadFile = Ret
End Function

' ��ȡCP���ݸ�ʽ
Private Function GetCPDataFormat() As String
   Dim Ret As String
   With UI_SHEET
      Dim TestEqp As String:   TestEqp = .Range("c3")            ' ��ȡ�����豸����
      Dim WaferType As String: WaferType = .Range("f3")          ' ��ȡ��Բ����
   End With
   Select Case TestEqp
   Case "MEX��ʽ"
      Ret = "MEX"
   Case "DCP��ʽ"
      Ret = "DCP"
   Case "CW��ʽ"
      Ret = IIf(WaferType = "MPW", "CWMW", "CWSW")               ' ���ݾ�Բ����ȷ���ǵ���Բ���ǶྦྷԲ
   End Select
   GetCPDataFormat = Ret
End Function

' �򿪶��������
Private Function OpendBooks(fList, Optional OpenFun) As Workbook()
   Dim Ret() As Workbook: ReDim Ret(LBound(fList) To UBound(fList))
   Dim i: For i = LBound(fList) To UBound(fList)
      If IsMissing(OpenFun) Then
         Set Ret(i) = Workbooks.Open(fList(i), False, True)      ' ��׼�򿪷�ʽ
      Else
         Set Ret(i) = Application.Run(OpenFun, fList(i))         ' ʹ�����⺯����
      End If
   Next
   OpendBooks = Ret
End Function

' ��ȡ���й������ĵ�һ��������
Private Function GetWaferDataSheets(DataBooks() As Workbook) As Worksheet()
   Dim Ret() As Worksheet: ReDim Ret(LBound(DataBooks) To UBound(DataBooks))
   Dim i: For i = LBound(DataBooks) To UBound(DataBooks)
      Set Ret(i) = DataBooks(i).Worksheets(1)                   ' ��ȡÿ���������ĵ�һ��������
   Next
   GetWaferDataSheets = Ret
End Function

' �ر����й�����
Private Function CloseBooks(DataBooks() As Workbook)
   Dim i: For i = LBound(DataBooks) To UBound(DataBooks)
      DataBooks(i).Close False                                  ' �رչ�����������
   Next
End Function

' ���������ݵ����������
Public Function FillTestData(ResultBook As Workbook, TestInfo As CPLot)
   Dim ResultSheet As Worksheet: Set ResultSheet = ResultBook.Worksheets("Data")
   With ResultSheet
      ListFill2Rng .Range("a1"), "Wafer,Seq,Bin,X,Y"            ' ����ͷ
      Dim Index: For Index = 1 To TestInfo.ParamCount
         .Cells(1, Index + 5).Value = TestInfo.Params(Index).Id  ' ������ID��Ϊ�б���
      Next
   End With
   With TestInfo
      Dim ParamCount As Integer: ParamCount = .ParamCount
      Dim FillRow As Long: FillRow = 2                          ' �ӵ�2�п�ʼ�������
      Dim i: For i = 1 To .WaferCount
         With .Wafers(i)
            Dim WaferRng As Range
            Set WaferRng = ResultSheet.Cells(FillRow, 1).Resize(.ChipCount)
            WaferRng.Value = .WaferId                           ' ��侧ԲID
            WaferRng.Offset(0, 1) = .Seq                        ' ������
            WaferRng.Offset(0, 2) = .Bin                        ' ���Binֵ
            WaferRng.Offset(0, 3) = .x                          ' ���X����
            WaferRng.Offset(0, 4) = .Y                          ' ���Y����
            Dim j: For j = 1 To ParamCount
               WaferRng.Offset(0, 4 + j) = .ChipDatas(j)        ' ����������
            Next
            FillRow = FillRow + .ChipCount                      ' ������һ��������ʼ��
         End With
      Next
   End With
End Function

' �������Ϣ�����������
Public Function FillSpec(ResultBook As Workbook, TestInfo As CPLot)
   Dim ResultSheet As Worksheet: Set ResultSheet = ResultBook.Worksheets("Spec")
   Dim x: ReDim x(1 To 4 + SizeOf(TestInfo.Params(1).TestCond), 1 To TestInfo.ParamCount)
   With TestInfo
      Dim Index: For Index = 1 To .ParamCount
         With .Params(Index)
            x(1, Index) = .Id                                    ' ����ID
            x(2, Index) = .Unit                                  ' ��λ
            x(3, Index) = .SL                                    ' ����
            x(4, Index) = .SU                                    ' ����
            Dim jj: jj = 5
            Dim j: For j = LBound(.TestCond) To UBound(.TestCond)
               x(jj, Index) = .TestCond(j)                       ' ��������
               jj = jj + 1
            Next
         End With
      Next
   End With
   
   With ResultSheet
      ListFill2Rng .Range("a1"), "Param,Unit,SL,SU,TestCond:", HorizontalFlag:=False  ' ����б���
      FillArray2Rng .Range("b1"), x                             ' ���������
   End With
End Function

' ��ȡ���в���ֵ�ķ�Χ
Private Function GetAllTestVal(DataSheet As Worksheet) As Range
   With DataSheet
      With .Range("a1").CurrentRegion
         Dim TotalRows As Long: TotalRows = .Rows.Count
         Dim TotalCols As Long: TotalCols = .Columns.Count
      End With
      Set GetAllTestVal = .Range(.Cells(2, 6), .Cells(TotalRows, TotalCols))  ' ���شӵ�2�е�6�п�ʼ����������
   End With
End Function

' ������ӱ��еľ�Բ�����Ƿ���ʵ��һ��
Private Function CheckFactWaferQty(TestInfo As CPLot) As Boolean
   Dim Ret As Boolean
   If INCLUDE_EXP_FACT_FLAG Then
      Dim ReadWafers: ReadWafers = TestInfo.WaferCount                        ' ʵ�ʾ�Բ����
      Dim SetupWafers: SetupWafers = FACTOR_SHEET.Range("a1").CurrentRegion.Rows.Count - 1  ' ���ӱ��еľ�Բ����
      Ret = (ReadWafers = SetupWafers)
      If False = Ret Then
         gShow.ErrAlarm Array("Ƭ�������Ϣ��,Ƭ��Ϊ" & SetupWafers, _
                               "���ļ���ȡ����Ƭ��Ϊ" & ReadWafers)           ' ������һ����ʾ����
      End If
   Else
      Ret = True
   End If
   CheckFactWaferQty = Ret
End Function

