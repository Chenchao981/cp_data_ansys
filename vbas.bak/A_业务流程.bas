Attribute VB_Name = "A_业务流程"
Option Explicit

' 工作表名称列表常量，用逗号分隔
Const SHEET_NAME_LIST As String = "Spec,Data,Yield,Summary,Map,BoxPlot,Scatter,ParamColorChart"

' 全局对象实例
Public gShow As New clsShowInfo  ' 信息显示类实例
Public RegEx As New clsRegEx     ' 正则表达式类实例

Dim ToolTimer                    ' 工具运行计时器
Dim BookSaved As Boolean         ' 工作簿是否已保存标志

' 根据CP数据格式获取文件列表
Private Function GetFileList(CPDataFormat As String)
   Dim Ret
   Select Case CPDataFormat
   Case "MEX"
      Ret = PickupFile("测试数据", True, "xls")        ' MEX格式，选择xls文件，可多选
   Case "DCP"
      Ret = PickupFile("测试数据", True, "txt")        ' DCP格式，选择txt文件，可多选
   Case "CWSW"
      Ret = PickupFile("测试数据", True, "csv")        ' CW单晶圆格式，选择csv文件，可多选
   Case "CWMW"
      Ret = PickupFile("测试数据", False, "csv")       ' CW多晶圆格式，选择csv文件，单选
   Case Else
   '
   End Select
   GetFileList = Ret
End Function

' 主函数，程序入口
Sub main()
   InitSheetSetup                                            ' 初始化工作表设置
   Dim CPDataFormat As String: CPDataFormat = GetCPDataFormat()  ' 获取CP数据格式
   
   Dim fList: fList = GetFileList(CPDataFormat): If IsEmpty(fList) Then Exit Sub  ' 获取文件列表，如果为空则退出
   
   StartMarco                                                ' 开始宏处理
   
   Dim TestInfo As CPLot: TestInfo = ReadFile(fList, CPDataFormat)  ' 读取文件数据
   If TestInfo.WaferCount = 0 Then Exit Sub                  ' 如果没有晶圆数据则退出
   If SetupCheck(TestInfo) = False Then gShow.ErrStop "设置存在错误", OCAP:="请重新设置后运行"  ' 检查设置，有错误则终止
   
   If ADD_CAL_DATA_FLAG Then AddCalData TestInfo            ' 如果需要，添加计算数据
   
   Dim ResultBook As Workbook: Set ResultBook = CreateResultBook(SHEET_NAME_LIST)  ' 创建结果工作簿
   FillSpec ResultBook, TestInfo                            ' 填充规格数据
   FillTestData ResultBook, TestInfo                        ' 填充测试数据
   ShowYield ResultBook, TestInfo                           ' 显示良率数据
   mySummary ResultBook, TestInfo                           ' 生成数据摘要
'
   If BOX_PLOT_FLAG Then
      PlotAllParamBoxChart ResultBook, TestInfo, CheckFactWaferQty(TestInfo)  ' 如果需要，绘制箱线图
   End If
   
   Dim myPPT As Object
   If BIN_MAP_PLOT_FLAG Then
      If myPPT Is Nothing Then Set myPPT = CreateResultPPT(TestInfo)  ' 创建结果PPT对象
      PlotAllMap ResultBook, TestInfo, myPPT                ' 绘制所有Bin图
   End If
'
   If DATA_COLOR_PLOT_FLAG Then
      Dim myColorPoint
      myColorPoint = ColorPointSetup(GetAllTestVal(ResultBook.Worksheets("Data")))  ' 设置颜色点
      If myPPT Is Nothing Then Set myPPT = CreateResultPPT(TestInfo)  ' 创建结果PPT对象
      PlotDataColor ResultBook, TestInfo, myPPT, myColorPoint  ' 绘制数据颜色图
   End If
'
   If SCATTER_PLOT_FLAG Then PlotScatterChart ResultBook, XY_SETUP_SHEET, TestInfo  ' 如果需要，绘制散点图
'
   Dim myReusltFileName As String: myReusltFileName = SaveResultBook(ResultBook, TestInfo.Product)  ' 保存结果工作簿
   If Not myPPT Is Nothing Then myPPT.Save                  ' 如果PPT存在，则保存PPT
   
   FinishMarco                                              ' 完成宏处理
   
End Sub

' 开始宏处理，设置状态和计时
Private Sub StartMarco()
   ToolTimer = Timer                            ' 记录开始时间
   BookSaved = ThisWorkbook.Saved               ' 保存当前工作簿状态
   'ShowPrompt
   Application.ScreenUpdating = False           ' 关闭屏幕更新
   Application.Calculation = xlCalculationManual ' 设置手动计算
End Sub

' 完成宏处理，恢复状态并显示完成信息
Private Sub FinishMarco()
   Application.Calculation = xlCalculationAutomatic ' 恢复自动计算
   Application.StatusBar = False                   ' 清除状态栏
   ThisWorkbook.Saved = BookSaved                  ' 恢复工作簿保存状态
   UI_SHEET.Activate                               ' 激活UI工作表
   MsgBox "finish" & vbLf & "time(s):" & _
      Format(Timer - ToolTimer, "0.0"), vbInformation + vbOKOnly  ' 显示完成信息和耗时
End Sub

' 检查各项设置是否正确
Private Function SetupCheck(TestInfo As CPLot) As Boolean
   Dim Ret As Boolean: Ret = True
   
   If ADD_CAL_DATA_FLAG Then
      If False = SetupCheck_ADD_CAL_DATA(TestInfo) Then Ret = False  ' 检查计算数据设置
   End If
   
   If BOX_PLOT_FLAG And INCLUDE_EXP_FACT_FLAG Then
      If False = CheckFactWaferQty(TestInfo) Then Ret = False        ' 检查实验因子设置
   End If
   
   If SCATTER_PLOT_FLAG Then
      If False = SetupCheck_SCATTER_PLOT(TestInfo) Then Ret = False  ' 检查散点图设置
   End If
   
   SetupCheck = Ret
End Function


' 保存结果工作簿到指定位置
Private Function SaveResultBook(Result As Workbook, Lot) As String
   Dim mySaveFileName As String
   Dim myPath As String
   myPath = ThisWorkbook.Path & "\整理后的数据文件\"      ' 设置保存路径
   If Dir(myPath, vbDirectory) = "" Then MkDir myPath    ' 如果路径不存在则创建
   mySaveFileName = myPath & Lot & ".xlsx"               ' 设置文件名
   If Dir(mySaveFileName) <> "" Then Kill mySaveFileName ' 如果文件已存在则删除
   Result.SaveAs mySaveFileName                          ' 保存工作簿
   SaveResultBook = mySaveFileName
End Function

' 显示操作提示信息
Private Sub ShowPrompt()
   Dim info() As String: ReDim info(1 To 6)
   info(1) = "说明"
   info(2) = "-------------------------------------------------"
   info(3) = "首先会弹出文件选择框,"
   info(4) = "请指定需要处理的csv数据文件"
   info(5) = "然后工具会将csv文件格式转换"
   info(6) = "并整理输出为xlsx文件"
   MsgBox Join(info, vbCrLf), vbOKOnly, "提示"          ' 显示操作说明
End Sub

' 读取文件数据
Private Function ReadFile(fList, CPDataFormat As String) As CPLot
   Dim Ret As CPLot
   Dim DataBooks() As Workbook
   If CPDataFormat = "DCP" Then
      DataBooks = OpendBooks(fList, "OpenTabTextxlDelimitedFile")  ' DCP格式使用特殊的打开方式
   Else
      DataBooks = OpendBooks(fList)                                ' 其他格式标准打开
   End If
       
   Dim WaferDataSheets() As Worksheet
   WaferDataSheets = GetWaferDataSheets(DataBooks)                ' 获取晶圆数据工作表
   If CPDataFormat = "CWMW" Then
      Ret.PassBin = 1
      SplitInfo_CWMW Ret, WaferDataSheets(1)                     ' CW多晶圆格式处理
   Else
      With Ret
         .WaferCount = UBound(WaferDataSheets) - LBound(WaferDataSheets) + 1  ' 设置晶圆数量
         ReDim .Wafers(1 To .WaferCount)
         Dim i: For i = LBound(WaferDataSheets) To UBound(WaferDataSheets)
            Select Case CPDataFormat
            Case "CWSW"
               .PassBin = 1
               SplitInfo_CWSW Ret, WaferDataSheets(i), i         ' CW单晶圆格式处理
            Case "MEX"
               .PassBin = 1
               SplitInfo_MEX Ret, WaferDataSheets(i), i          ' MEX格式处理
            Case "DCP"
               .PassBin = 1
               SplitInfo_DCP Ret, WaferDataSheets(i), i          ' DCP格式处理
            Case Else
               MsgBox "未定义的格式", vbCritical, "终止运行"     ' 未知格式报错
               Exit For
            End Select
         Next
      End With
   End If
   CloseBooks DataBooks                                          ' 关闭数据工作簿
   ReadFile = Ret
End Function

' 获取CP数据格式
Private Function GetCPDataFormat() As String
   Dim Ret As String
   With UI_SHEET
      Dim TestEqp As String:   TestEqp = .Range("c3")            ' 获取测试设备类型
      Dim WaferType As String: WaferType = .Range("f3")          ' 获取晶圆类型
   End With
   Select Case TestEqp
   Case "MEX格式"
      Ret = "MEX"
   Case "DCP格式"
      Ret = "DCP"
   Case "CW格式"
      Ret = IIf(WaferType = "MPW", "CWMW", "CWSW")               ' 根据晶圆类型确定是单晶圆还是多晶圆
   End Select
   GetCPDataFormat = Ret
End Function

' 打开多个工作簿
Private Function OpendBooks(fList, Optional OpenFun) As Workbook()
   Dim Ret() As Workbook: ReDim Ret(LBound(fList) To UBound(fList))
   Dim i: For i = LBound(fList) To UBound(fList)
      If IsMissing(OpenFun) Then
         Set Ret(i) = Workbooks.Open(fList(i), False, True)      ' 标准打开方式
      Else
         Set Ret(i) = Application.Run(OpenFun, fList(i))         ' 使用特殊函数打开
      End If
   Next
   OpendBooks = Ret
End Function

' 获取所有工作簿的第一个工作表
Private Function GetWaferDataSheets(DataBooks() As Workbook) As Worksheet()
   Dim Ret() As Worksheet: ReDim Ret(LBound(DataBooks) To UBound(DataBooks))
   Dim i: For i = LBound(DataBooks) To UBound(DataBooks)
      Set Ret(i) = DataBooks(i).Worksheets(1)                   ' 获取每个工作簿的第一个工作表
   Next
   GetWaferDataSheets = Ret
End Function

' 关闭所有工作簿
Private Function CloseBooks(DataBooks() As Workbook)
   Dim i: For i = LBound(DataBooks) To UBound(DataBooks)
      DataBooks(i).Close False                                  ' 关闭工作簿不保存
   Next
End Function

' 填充测试数据到结果工作簿
Public Function FillTestData(ResultBook As Workbook, TestInfo As CPLot)
   Dim ResultSheet As Worksheet: Set ResultSheet = ResultBook.Worksheets("Data")
   With ResultSheet
      ListFill2Rng .Range("a1"), "Wafer,Seq,Bin,X,Y"            ' 填充表头
      Dim Index: For Index = 1 To TestInfo.ParamCount
         .Cells(1, Index + 5).Value = TestInfo.Params(Index).Id  ' 填充参数ID作为列标题
      Next
   End With
   With TestInfo
      Dim ParamCount As Integer: ParamCount = .ParamCount
      Dim FillRow As Long: FillRow = 2                          ' 从第2行开始填充数据
      Dim i: For i = 1 To .WaferCount
         With .Wafers(i)
            Dim WaferRng As Range
            Set WaferRng = ResultSheet.Cells(FillRow, 1).Resize(.ChipCount)
            WaferRng.Value = .WaferId                           ' 填充晶圆ID
            WaferRng.Offset(0, 1) = .Seq                        ' 填充序号
            WaferRng.Offset(0, 2) = .Bin                        ' 填充Bin值
            WaferRng.Offset(0, 3) = .x                          ' 填充X坐标
            WaferRng.Offset(0, 4) = .Y                          ' 填充Y坐标
            Dim j: For j = 1 To ParamCount
               WaferRng.Offset(0, 4 + j) = .ChipDatas(j)        ' 填充参数数据
            Next
            FillRow = FillRow + .ChipCount                      ' 更新下一次填充的起始行
         End With
      Next
   End With
End Function

' 填充规格信息到结果工作簿
Public Function FillSpec(ResultBook As Workbook, TestInfo As CPLot)
   Dim ResultSheet As Worksheet: Set ResultSheet = ResultBook.Worksheets("Spec")
   Dim x: ReDim x(1 To 4 + SizeOf(TestInfo.Params(1).TestCond), 1 To TestInfo.ParamCount)
   With TestInfo
      Dim Index: For Index = 1 To .ParamCount
         With .Params(Index)
            x(1, Index) = .Id                                    ' 参数ID
            x(2, Index) = .Unit                                  ' 单位
            x(3, Index) = .SL                                    ' 下限
            x(4, Index) = .SU                                    ' 上限
            Dim jj: jj = 5
            Dim j: For j = LBound(.TestCond) To UBound(.TestCond)
               x(jj, Index) = .TestCond(j)                       ' 测试条件
               jj = jj + 1
            Next
         End With
      Next
   End With
   
   With ResultSheet
      ListFill2Rng .Range("a1"), "Param,Unit,SL,SU,TestCond:", HorizontalFlag:=False  ' 填充行标题
      FillArray2Rng .Range("b1"), x                             ' 填充规格数据
   End With
End Function

' 获取所有测试值的范围
Private Function GetAllTestVal(DataSheet As Worksheet) As Range
   With DataSheet
      With .Range("a1").CurrentRegion
         Dim TotalRows As Long: TotalRows = .Rows.Count
         Dim TotalCols As Long: TotalCols = .Columns.Count
      End With
      Set GetAllTestVal = .Range(.Cells(2, 6), .Cells(TotalRows, TotalCols))  ' 返回从第2行第6列开始的数据区域
   End With
End Function

' 检查因子表中的晶圆数量是否与实际一致
Private Function CheckFactWaferQty(TestInfo As CPLot) As Boolean
   Dim Ret As Boolean
   If INCLUDE_EXP_FACT_FLAG Then
      Dim ReadWafers: ReadWafers = TestInfo.WaferCount                        ' 实际晶圆数量
      Dim SetupWafers: SetupWafers = FACTOR_SHEET.Range("a1").CurrentRegion.Rows.Count - 1  ' 因子表中的晶圆数量
      Ret = (ReadWafers = SetupWafers)
      If False = Ret Then
         gShow.ErrAlarm Array("片号相关信息中,片数为" & SetupWafers, _
                               "而文件读取到的片数为" & ReadWafers)           ' 数量不一致显示警告
      End If
   Else
      Ret = True
   End If
   CheckFactWaferQty = Ret
End Function

