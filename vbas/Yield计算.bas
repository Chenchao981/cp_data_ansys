Attribute VB_Name = "Yield??" ' Module name suggests "Yield Calculation"
Option Explicit

' ???? Wafer ? Bin ???????????? "Yield" ???
Public Function ShowYield(ResultBook As Workbook, _
                          TestInfo As CPLot)
   If TestInfo.WaferCount = 0 Then Exit Function ' ???? Wafer ??????
   
   Dim ResultSheet As Worksheet: Set ResultSheet = ResultBook.Worksheets("Yield")
   If ResultSheet Is Nothing Then
       gShow.ErrStop "???? Yield ????"
       Exit Function
   End If
   ResultSheet.Cells.ClearContents ' ?????
   
   ' 1. ???? Wafer ? Bin ???? (??????)
   Dim WaferBinDics() As Object
   WaferBinDics = CalYield(TestInfo)
   
   ' 2. ???? Wafer ???? Bin ?????????? (PassBin ???????)
   Dim AllBinList: AllBinList = GetAllBinList(WaferBinDics, TestInfo.PassBin)
   If Not IsArray(AllBinList) Then Exit Function ' ???? Bin ??????
   
   Dim BinStartCol As Long: BinStartCol = 4 ' Bin ???????? (D?)
   Dim BinCount As Long: BinCount = SizeOf(AllBinList)
   If BinCount = 0 Then Exit Function
   
   ' 3. ????????? Bin ???? (????)
   Dim BinResultData: BinResultData = GetContent(WaferBinDics, AllBinList)
   
   With ResultSheet
      ' 4. ????
      Dim HeadList: HeadList = Array("Wafer", "Yield", "Total", "Pass")
      ListFill2Rng .Range("a1"), HeadList ' ?? A1:D1
      .Cells(1, BinStartCol).Value = "Pass" ' ?? D ???? "Pass"
      Dim i As Long
      For i = 1 To BinCount - 1 ' ???? Bin ???? Bin ??? (E???)
         .Cells(1, BinStartCol + i).Value = "Bin" & AllBinList(LBound(AllBinList) + i)
      Next
      
      ' 5. ???? Wafer ? Bin ????
      FillArray2Rng .Cells(2, BinStartCol), BinResultData
      
      ' 6. ?? Wafer ID (A?)
      For i = 1 To TestInfo.WaferCount
         .Cells(i + 1, 1).Value = TestInfo.Wafers(i).WaferId & "#"
      Next
      
      ' 7. ????? "All" ? (???? Wafer ? Bin ??)
      Dim TotalRow As Long: TotalRow = .Range("a1").CurrentRegion.Rows.Count + 1
      .Cells(TotalRow, 1).Value = "All"
      Dim SummaryCols As Long: SummaryCols = .Range("a1").CurrentRegion.Columns.Count
      Dim j As Long
      For j = BinStartCol To SummaryCols ' ? Pass ????????
         .Cells(TotalRow, j).Formula = "=SUM(" & .Range(.Cells(2, j), .Cells(TotalRow - 1, j)).Address & ")"
      Next
      
      ' 8. ??????? Wafer ????? Total ? Yield
      For i = 2 To TotalRow
         ' ?? Total (C?) = Sum(D? ?????? Bin ?)
         .Cells(i, 3).Formula = "=SUM(" & .Range(.Cells(i, BinStartCol), .Cells(i, SummaryCols)).Address & ")"
         ' ?? Yield (B?) = Pass (D?) / Total (C?)
         If .Cells(i, 3).Value <> 0 Then ' ??????
             .Cells(i, 2).Value = .Cells(i, 4).Value / .Cells(i, 3).Value
             .Cells(i, 2).NumberFormat = "0.00%" ' ???????
         Else
             .Cells(i, 2).Value = "N/A"
         End If
      Next
      
      ' 9. ??????????????
      .UsedRange.Value = .UsedRange.Value
      .UsedRange.Columns.AutoFit
   End With
End Function

' ???? Wafer ? Bin ??????????????
' ????? Key ? Bin ??Value ?? Bin ???
Private Function CalYield(TestInfo As CPLot) As Object()
   Dim WaferBinDics() As Object
   With TestInfo
      If .WaferCount = 0 Then Exit Function
      ReDim WaferBinDics(1 To .WaferCount) ' ????????? Wafer ??
      Dim i: For i = 1 To .WaferCount
         Set WaferBinDics(i) = CreateBinDic(.Wafers(i)) ' ??? Wafer ?? Bin ??
      Next
   End With
   CalYield = WaferBinDics
End Function

' ??? Wafer ?? Bin ????
Private Function CreateBinDic(toCalWafer As CPWafer) As Object
   Dim Ret As Object: Set Ret = CreateObject("scripting.dictionary")
   Ret.CompareMode = vbTextCompare ' ?? Bin ?????????
   With toCalWafer
      If Not IsArray(.Bin) Or .ChipCount = 0 Then Set CreateBinDic = Ret: Exit Function
      Dim i: For i = 1 To .ChipCount
         Dim myBin As Variant: myBin = .Bin(i, 1)
         If Not IsEmpty(myBin) Then ' ?????? Bin ?
             If Ret.exists(myBin) Then
                Ret(myBin) = Ret(myBin) + 1
             Else
                Ret.Add myBin, 1
             End If
         End If
      Next
   End With
   Set CreateBinDic = Ret
End Function

' ???? Wafer ? Bin ???? (WaferBinDics) ???? Bin ?? (AllBinList)?
' ?????????????? "Yield" ???? Bin ????
' ???????: (Wafer ??) x (Bin ??)
Private Function GetContent(WaferBinDics() As Object, AllBinList)
   Dim x
   Dim WaferLBound As Long: WaferLBound = LBound(WaferBinDics)
   Dim WaferUBound As Long: WaferUBound = UBound(WaferBinDics)
   Dim BinLBound As Long: BinLBound = LBound(AllBinList)
   Dim BinUBound As Long: BinUBound = UBound(AllBinList)
   
   ReDim x(WaferLBound To WaferUBound, BinLBound To BinUBound)
   
   Dim i: For i = WaferLBound To WaferUBound
      If Not WaferBinDics(i) Is Nothing Then ' ????????
          With WaferBinDics(i)
             Dim j: For j = BinLBound To BinUBound
                If .exists(AllBinList(j)) Then
                   x(i, j) = WaferBinDics(i)(AllBinList(j))
                Else
                   x(i, j) = 0 ' ??? Wafer ???? Bin???? 0
                End If
             Next
          End With
      End If
   Next
   GetContent = x
End Function

' ???? Wafer ???? Bin ???????????
Private Function GetAllBinList(WaferBinDics() As Object, _
                               PassBinId)
   ' 1. ???? Wafer ??? Key ??? List
   Dim Ret: Ret = MergeDicsKey2List(WaferBinDics)
   If Not IsArray(Ret) Then Exit Function
   ' 2. ? Bin List ???? (Pass Bin ??????????)
   SortBinList Ret, PassBinId
   GetAllBinList = Ret
End Function

' ? Bin ???????PassBinId ???????????????
' ?????????????? PassBinId ????
Private Sub SortBinList(BinList, PassBinId)
    If Not IsArray(BinList) Then Exit Sub
    Dim iOuter As Long, iInner As Long
    Dim iLBound As Long, iUBound As Long
    iLBound = LBound(BinList)
    iUBound = UBound(BinList)
    If iLBound >= iUBound Then Exit Sub ' ???????????????
    
    Dim PassBinFound As Boolean: PassBinFound = False
    Dim PassBinIndex As Long
    
    ' ???? (??)
    For iOuter = iLBound To iUBound - 1
        For iInner = iLBound To iUBound - (iOuter - iLBound) - 1
            ' ???? PassBin
            If Not PassBinFound Then
                If BinList(iInner) = PassBinId Then
                    PassBinFound = True
                    PassBinIndex = iInner
                End If
                If BinList(iInner + 1) = PassBinId Then
                    PassBinFound = True
                    PassBinIndex = iInner + 1
                End If
            End If
            
            ' ????? (?????????????????????)
            On Error Resume Next
            Dim Val1: Val1 = CDbl(BinList(iInner))
            Dim Val2: Val2 = CDbl(BinList(iInner + 1))
            If Err.Number = 0 Then ' ???????
                If Val1 > Val2 Then Swap BinList, iInner, iInner + 1
            Else ' ??????
                If CStr(BinList(iInner)) > CStr(BinList(iInner + 1)) Then Swap BinList, iInner, iInner + 1
            End If
            On Error GoTo 0
        Next iInner
    Next iOuter
    
    ' ????? PassBin??????????
    If PassBinFound Then
        If PassBinIndex <> iLBound Then
            Dim PassBinValue: PassBinValue = BinList(PassBinIndex)
            ' ? PassBinIndex ?????????
            For iInner = PassBinIndex To iLBound + 1 Step -1
                BinList(iInner) = BinList(iInner - 1)
            Next
            BinList(iLBound) = PassBinValue ' ? PassBin ????
        End If
    End If
End Sub

' ????????????
Private Sub Swap(BinList, i1, i2)
   Dim tmp
   tmp = BinList(i1)
   BinList(i1) = BinList(i2)
   BinList(i2) = tmp
End Sub

' ?? SortBinList ??????
Private Sub test_SortBinList()
   Dim x: x = Split("bin1,bin3,bin9,bin2,bin0", ",")
   SortBinList x, "bin0"
   Debug.Print Join(x, ",") = "bin0,bin1,bin2,bin3,bin9" ' ????
   
   Dim y: y = Array(5, 1, 10, 2, 8, 0)
   SortBinList y, 0
   Debug.Print Join(y, ",") = "0,1,2,5,8,10" ' ????
End Sub

' ??????? Key ??? List (??) ???????
Private Function MergeDicsKey2List(toMergeDics() As Object)
   Dim Ret
   Dim AllDic As Object: Set AllDic = CreateObject("scripting.dictionary")
   AllDic.CompareMode = vbTextCompare ' Key ??????
   
   Dim i: For i = LBound(toMergeDics) To UBound(toMergeDics)
      If Not toMergeDics(i) Is Nothing Then ' ????????
          Dim Keys: Keys = toMergeDics(i).Keys
          If IsArray(Keys) Then
              Dim Index: For Index = LBound(Keys) To UBound(Keys)
                 If Not AllDic.exists(Keys(Index)) Then
                    AllDic.Add Keys(Index), 0 ' ??????? Key
                 End If
              Next
          End If
      End If
   Next
   
   If AllDic.Count > 0 Then Ret = AllDic.Keys Else Ret = Empty
   MergeDicsKey2List = Ret
End Function
