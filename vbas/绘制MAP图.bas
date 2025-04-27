Attribute VB_Name = "??MAP?" ' Module name suggests "Draw MAP Chart"
Option Explicit

' ???????? Wafer ? Bin Map ?? "Map" ?????????? Wafer Map ??? PPT ?
Public Sub PlotAllMap(w As Workbook, myTestinfo As CPLot, myPPT As Object)
   ' 1. ? BIN_SETUP_SHEET ?? Bin ?????????
   Dim BinColorDic As Object: Set BinColorDic = CreateBinColorDic(BIN_SETUP_SHEET)
   If BinColorDic Is Nothing Or BinColorDic.Count = 0 Then
       gShow.ErrAlarm "???? Bin ???? (BIN_SETUP_SHEET)????? MAP ??"
       Exit Sub
   End If
   
   Dim MapSheet As Worksheet: Set MapSheet = w.Worksheets("Map")
   With MapSheet
      Dim StartCell As Range: Set StartCell = .Range("b2") ' MAP ?????????
      ' 2. ???? Wafer
      Dim WaferIndex: For WaferIndex = 1 To myTestinfo.WaferCount
         Application.StatusBar = "??MAP?..." & myTestinfo.Wafers(WaferIndex).WaferId & "#"
         StartCell.Offset(-1, -1) = myTestinfo.Wafers(WaferIndex).WaferId & "#" ' ?????? Wafer ID
         ' 3. ???? Wafer ? Bin Map ? MapSheet???????????
         Dim h: h = PlotBinMap(StartCell, myTestinfo.Wafers(WaferIndex), BinColorDic, myPPT)
         ' 4. ????? Wafer Map ???????? (???? h + 2 ?)
         Set StartCell = StartCell.Offset(h + 2, 0)
      Next
      
      ' 5. ??? MapSheet
      .Activate
      ActiveWindow.DisplayGridlines = False
      .Columns(1).ColumnWidth = 20 ' ?? A ???
      ' 6. ? BIN_SETUP_SHEET ???????????? MapSheet ????
      CopyColorSetup MapSheet
      .Range("a1").Activate
      If .Shapes.Count > 0 Then ' ?????????
         With .Shapes(.Shapes.Count) ' ???????????
            .ScaleHeight 0.5, msoTrue ' ????
            .Top = 30
            .CopyPicture ' ???????????? PPT
         End With
      Else
          gShow.ErrAlarm "???? Bin ????? Map ????"
      End If
   End With
   
   ' 7. ????????? PPT ?? 2 ???? (Bin Map Slide)
   On Error Resume Next
   Dim LegendShape As Object: Set LegendShape = myPPT.slides(2).Shapes.Paste
   If Err.Number = 0 And Not LegendShape Is Nothing Then
       LegendShape.Left = 10
       LegendShape.Top = 40
   Else
       gShow.ErrAlarm "???? Bin ????? PPT?"
   End If
   On Error GoTo 0
  
End Sub

' ? Bin ?????? (BIN_SETUP_SHEET) ?????????????? (Target)
Private Function CopyColorSetup(Target As Worksheet)
   On Error Resume Next
   BIN_SETUP_SHEET.Range("a1").CurrentRegion.CopyPicture
   If Err.Number <> 0 Then
       gShow.ErrAlarm "???? Bin ???????"
       Exit Function
   End If
   Target.Paste
   If Err.Number <> 0 Then
       gShow.ErrAlarm "???? Bin ?????????????"
   End If
   On Error GoTo 0
End Function

' ???? Wafer ? Bin Map ? Excel ???????? PPT ?
' StartCell: ? Excel ??? Map ???????
' myWaferInfo: ?? Wafer ???
' BinColorDic: Bin ?????????
' myPPT: PowerPoint ??
' ???: ??? Map ? Excel ??????
Private Function PlotBinMap(StartCell As Range, myWaferInfo As CPWafer, BinColorDic As Object, myPPT As Object)
   Dim x, Y, Bin, a
   Bin = myWaferInfo.Bin
   x = myWaferInfo.x
   Y = myWaferInfo.Y
   
   ' ???????
   If Not IsArray(x) Or Not IsArray(Y) Or Not IsArray(Bin) Then PlotBinMap = 0: Exit Function
   If UBound(x) <> UBound(Y) Or UBound(x) <> UBound(Bin) Then PlotBinMap = 0: Exit Function
   If myWaferInfo.ChipCount = 0 Then PlotBinMap = 0: Exit Function
   
   On Error Resume Next ' ?? Min/Max ????? (?????)
   Dim MinX: MinX = Application.WorksheetFunction.Min(x)
   Dim MaxX: MaxX = Application.WorksheetFunction.Max(x)
   Dim MinY: MinY = Application.WorksheetFunction.Min(Y)
   Dim MaxY: MaxY = Application.WorksheetFunction.Max(Y)
   If Err.Number <> 0 Then PlotBinMap = 0: Exit Function ' ???? Min/Max ??????
   On Error GoTo 0
   
   ' ?? Excel ? Map ??????
   SetMapCellSize StartCell, MinY, MaxY, MinX, MaxX
   
   ' ???????? d???? Wafer ? X, Y ????
   Dim MapHeight As Long: MapHeight = MaxY - MinY
   Dim MapWidth As Long: MapWidth = MaxX - MinX
   Dim d: ReDim d(0 To MapHeight, 0 To MapWidth)
   
   ' ??? Chip ? Bin ?????? d ????? (?? Y ????X ???)
   Dim i: For i = 1 To UBound(x)
      Dim xx As Integer: xx = x(i, 1) - MinX ' X ????????? (0-based)
      Dim yy As Integer: yy = Y(i, 1) - MinY ' Y ????????? (0-based)
      ' ???????????? (????????????)
      If yy >= 0 And yy <= MapHeight And xx >= 0 And xx <= MapWidth Then
          d(yy, MaxX - x(i, 1)) = Bin(i, 1) ' X?????? d(y, MaxX-x)
      End If
   Next
   
   ' ??? d ????? Excel ? Map ??
   Dim MapRng As Range: Set MapRng = StartCell.Resize(MapHeight + 1, MapWidth + 1)
   MapRng.Value = d
   'MapRng.Borders.LineStyle = xlContinuous ' ???????
   
   ' ?? Bin ?????? (??)
   SetBinMapFormatCondtions MapRng, BinColorDic
   
   ' ????? Excel Map ????? PPT ?? 2 ???? (Bin Map Slide)
   AddMap MapRng, myPPT.slides(2), CInt(myWaferInfo.WaferId)
   
   ' ?? Map ? Excel ??????
   PlotBinMap = MapHeight + 1
End Function

' ? Bin ??????? (ColorSetupSheet) ?? Bin ?????????
Private Function CreateBinColorDic(ColorSetupSheet As Worksheet) As Object
   Dim Ret As Object: Set Ret = CreateObject("scripting.dictionary")
   On Error Resume Next
   Dim SetupRange As Range: Set SetupRange = ColorSetupSheet.Range("a1").CurrentRegion
   If Err.Number <> 0 Or SetupRange Is Nothing Then
       Set CreateBinColorDic = Nothing: Exit Function
   End If
   
   Dim RowCount As Long: RowCount = SetupRange.Rows.Count
   If RowCount < 2 Then Set CreateBinColorDic = Nothing: Exit Function ' ???????????
   
   With ColorSetupSheet
      Dim i: For i = 2 To RowCount ' ?? 2 ?????
         Dim BinVal: BinVal = .Cells(i, 1).Value ' ? 1 ?? Bin ?
         Dim BinColor As Long: BinColor = .Cells(i, 2).Interior.Color ' ? 2 ????????
         If Not Ret.exists(BinVal) Then ' ??????
            Ret.Add BinVal, BinColor
         End If
      Next
   End With
   On Error GoTo 0
   Set CreateBinColorDic = Ret
End Function

' ?? Excel ????? Map ????????????
Private Sub SetMapCellSize(StartCell As Range, Min_Py, Max_Py, Min_Px, Max_Px)
   Dim MapCellHeight As Double, MapCellWidth As Double
   Dim HeightFactor As Long: HeightFactor = Max_Py - Min_Py + 1
   Dim WidthFactor As Long: WidthFactor = Max_Px - Min_Px + 1
   
   If HeightFactor <= 0 Or WidthFactor <= 0 Then Exit Sub ' ??????
   
   MapCellHeight = gMapHeight / HeightFactor
   MapCellWidth = 0.125 * gMapWidth / WidthFactor ' ??? 0.125 ??????????????????
   
   ' ?????????
   If MapCellHeight <= 0 Then MapCellHeight = 1
   If MapCellWidth <= 0 Then MapCellWidth = 1
   
   On Error Resume Next
   With StartCell.Resize(HeightFactor, WidthFactor)
      .ColumnWidth = MapCellWidth
      .RowHeight = MapCellHeight
   End With
   On Error GoTo 0
End Sub

