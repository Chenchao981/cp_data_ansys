Attribute VB_Name = "�ϲ���ppt��"
Option Explicit

' ȫ�ֱ�������;�������������ڼ�ʱ?
Dim myTimer

' �������ɵ� PPT �ļ�
' myPPT: PowerPoint Presentation ����
' Lot: Lot ���ƣ����ڹ����ļ���
Private Function SaveResultPPT(myPPT As Object, Lot) As String
   Dim mySaveFileName As String
   Dim myPath As String
   myPath = ThisWorkbook.Path & "\������MAP����\" ' ���屣��·��
   If Dir(myPath, vbDirectory) = "" Then MkDir myPath ' ���·���������򴴽�
   mySaveFileName = myPath & Lot & ".pptm" ' ���������ļ��� (����Ϊ���ú����ʾ�ĸ�)
   
   On Error Resume Next ' ����ɾ���ͱ���ʱ���ܷ����Ĵ���
   If Dir(mySaveFileName) <> "" Then Kill mySaveFileName ' ����ļ��Ѵ�����ɾ��
   myPPT.SaveAs mySaveFileName, ppSaveAsPresForReview ' ���� PPT (PresForReview��ʽ? ͨ����ppSaveAsDefault��ppSaveAsOpenXMLPresentation)
   If Err.Number <> 0 Then
       gShow.ErrAlarm "���� PPT �ļ�ʧ��: " & mySaveFileName & vbCrLf & Err.Description
       SaveResultPPT = ""
   Else
       SaveResultPPT = mySaveFileName
   End If
   On Error GoTo 0
End Function

' Ϊÿ�������� PPT �д���һ�Żõ�Ƭ (ͨ������ģ��õ�Ƭʵ��)
Private Function CreateParamSlides(myTestinfo As CPLot, myPPT As Object)
   On Error Resume Next
   Dim TemplateSlide As Object: Set TemplateSlide = myPPT.slides(2) ' ����� 2 ����ģ��õ�Ƭ
   If TemplateSlide Is Nothing Then
       gShow.ErrAlarm "�޷��ҵ� PPT ģ��õ�Ƭ (�� 2 ��)��"
       Exit Function
   End If
   
   With myTestinfo
      Dim i: For i = 1 To .ParamCount
         ' ����ģ��õ�Ƭ���»õ�Ƭ����뵽ģ��֮��
         Dim NewSlideIndex As Long: NewSlideIndex = TemplateSlide.Duplicate.SlideIndex
         ' ���¸��ƵĻõ�Ƭ�ƶ������ (��ѡ����ǰ�߼��ǰ�˳�����)
         ' myPPT.Slides(NewSlideIndex).MoveTo myPPT.Slides.Count
      Next
      
      ' Ϊ�´����Ĳ����õ�Ƭ (�ӵ� 3 �ſ�ʼ) ���ñ���
      For i = 1 To .ParamCount
         If i + 2 <= myPPT.Slides.Count Then
             Dim mySlide As Object: Set mySlide = myPPT.slides(i + 2)
             With .Params(i)
                AddTitle mySlide, .Id & "[" & .Unit & "] Map" ' ��ӱ��⣬���� "Param1[V] Map"
             End With
         Else
             gShow.ErrAlarm "���������õ�Ƭʱ����������Χ: " & i + 2
             Exit For
         End If
      Next
   End With
   On Error GoTo 0
End Function

' ��������ʼ�� PPT ����ļ�
Public Function CreateResultPPT(myTestinfo As CPLot) As Object
   Dim pptApp As Object
   On Error Resume Next
   Set pptApp = GetObject(, "Powerpoint.Application") ' ���Ի�ȡ�����е� PowerPoint ʵ��
   If Err.Number <> 0 Then
       Set pptApp = CreateObject("Powerpoint.Application") ' ���δ���У��򴴽���ʵ��
   End If
   On Error GoTo 0
   If pptApp Is Nothing Then
       gShow.ErrStop "�޷����������� PowerPoint Ӧ�ó���"
       Set CreateResultPPT = Nothing: Exit Function
   End If
   
   pptApp.Visible = True ' ʹ PowerPoint Ӧ�ó���ɼ�
   
   Dim myPPT As Object
   Dim TemplatePath As String: TemplatePath = ThisWorkbook.Path & "\WaferMap.potm" ' ģ���ļ�·��
   If Dir(TemplatePath) = "" Then
       gShow.ErrStop "�Ҳ��� PowerPoint ģ���ļ�: " & TemplatePath
       Set CreateResultPPT = Nothing: Exit Function
   End If
   
   On Error Resume Next
   Set myPPT = pptApp.Presentations.Open(TemplatePath)
   If Err.Number <> 0 Or myPPT Is Nothing Then
       gShow.ErrStop "�� PowerPoint ģ���ļ�ʧ��: " & TemplatePath & vbCrLf & Err.Description
       Set CreateResultPPT = Nothing: Exit Function
   End If
   On Error GoTo 0
   
   ' 1. ��� PPT ��ҳ����
   AddTitle2PPT myPPT, myTestinfo.Product
   ' 2. ��� Bin Map �õ�Ƭ���� (����ģ���2ҳ���� Bin Map)
   AddBinMapSlide myPPT
   ' 3. ���ݲ�����������ģ��õ�Ƭ�����ñ���
   CreateParamSlides myTestinfo, myPPT
   
   ' 4. ���� PPT �ļ� (ע��������ǰ���棬���� AddMap ������޸�)
   ' SaveResultPPT myPPT, myTestinfo.Product ' �����Ƶ��������������ɺ��ٱ���
   
   Set CreateResultPPT = myPPT
End Function

' (�˺����ƺ�δ�����ã��ҹ��ܲ�����)
' Ϊ��ӵ� PPT �� Wafer Map ͼƬ��Ӻ궯�� (�����ʱ���� "ClickWafer" + WaferId ��)
Private Function AddAnimation2Map(mySlide As Object, WaferMap As Object, WaferId)
   ' ע��: �˹���Ҫ�󱣴�Ϊ .pptm ��ʽ�����ҽ��շ�����ִ�к�
   On Error Resume Next
   With WaferMap.ActionSettings(ppMouseClick)
      .Action = ppActionRunMacro
      .Run = "ClickWafer" & WaferId
   End With
   On Error GoTo 0
End Function

' ��ָ���� PPT �õ�Ƭ�в���Ԥ��� 5x5 ��� (���ڶ�λ Wafer Map ��λ��)
Private Function GetSlideWaferTable(mySlide As Object) As Object
   Dim Ret As Object
   Dim myShape As Object
   On Error Resume Next
   For Each myShape In mySlide.Shapes
      If myShape.HasTable Then
         Dim myTable As Object: Set myTable = myShape.Table
         If myTable.Columns.Count = 5 And myTable.Rows.Count = 5 Then
            Set Ret = myTable: Exit For
         End If
      End If
   Next
   On Error GoTo 0
   Set GetSlideWaferTable = Ret
End Function

' ���� WaferId �� 5x5 ����м����Ӧ�ĵ�Ԫ�� Shape ����
Private Function GetWaferCell(myTable As Object, WaferId) As Object
   If myTable Is Nothing Then Exit Function
   ' WaferId �� 1 ��ʼ����
   Dim myRow As Long: myRow = (WaferId - 1) \ 5 + 1 ' �����к� (1-based)
   Dim myCol As Long: myCol = (WaferId - 1) Mod 5 + 1 ' �����к� (1-based)
   
   On Error Resume Next
   Set GetWaferCell = myTable.Cell(myRow, myCol).Shape
   On Error GoTo 0
End Function

' �� Excel �е� Map ��Χ (MapRng) ����ΪͼƬ��ճ����ָ�� PPT �õ�Ƭ (mySlide) �Ķ�Ӧ Wafer λ��
Public Function AddMap(MapRng As Range, mySlide As Object, WaferId) As Object
   Dim Ret As Object
   ' 1. �ڻõ�Ƭ�в��� 5x5 ���
   Dim SlideTable As Object: Set SlideTable = GetSlideWaferTable(mySlide)
   If SlideTable Is Nothing Then
       gShow.ErrAlarm "�ڻõ�Ƭ " & mySlide.SlideIndex & " ��δ�ҵ� 5x5 Wafer ���"
       Exit Function
   End If
   ' 2. ���� WaferId ��ȡĿ�굥Ԫ��
   Dim myCell As Object: Set myCell = GetWaferCell(SlideTable, WaferId)
   If myCell Is Nothing Then
       gShow.ErrAlarm "�ڻõ�Ƭ " & mySlide.SlideIndex & " �ı����δ�ҵ� Wafer " & WaferId & " �ĵ�Ԫ��"
       Exit Function
   End If
   
   Application.ScreenUpdating = True ' ȷ�� Excel �����������ȷ����ͼƬ
   On Error Resume Next
   ' 3. �� Excel ��Χ����ΪͼƬ (xlScreen, xlBitmap)
   MapRng.CopyPicture Appearance:=xlScreen, Format:=xlBitmap
   If Err.Number <> 0 Then
       gShow.ErrAlarm "���� Wafer Map ͼƬʧ�� (Wafer " & WaferId & ")��"
       Exit Function
   End If
   
   ' 4. ��ͼƬճ���� PPT �õ�Ƭ
   Dim myMapShape As Object: Set myMapShape = mySlide.Shapes.Paste
   If Err.Number <> 0 Or myMapShape Is Nothing Then
       gShow.ErrAlarm "ճ�� Wafer Map ͼƬʧ�� (Wafer " & WaferId & ") ���õ�Ƭ " & mySlide.SlideIndex & "��"
       Application.CutCopyMode = False
       Exit Function
   End If
   Application.CutCopyMode = False ' ���������
   
   ' 5. ����ճ����ͼƬ��С��λ�ã�ʹ����ӦĿ�굥Ԫ��
   With myMapShape
      .Name = "Map" & WaferId
      ' ��������������Ӧ��Ԫ���Ȼ�߶ȣ�������
      Dim CellWidth As Single: CellWidth = myCell.Width - 5 ' �����߾�
      Dim CellHeight As Single: CellHeight = myCell.Height - 5
      Dim Ratio As Single
      If (.Width / CellWidth) > (.Height / CellHeight) Then
          Ratio = CellWidth / .Width
      Else
          Ratio = CellHeight / .Height
      End If
      .ScaleWidth Ratio, msoTrue
      .ScaleHeight Ratio, msoTrue
      .Left = myCell.Left + (myCell.Width - .Width) / 2
      .Top = myCell.Top + (myCell.Height - .Height) / 2
   End With
   
   ' 6. (��ѡ) ��Ӻ궯��
   ' AddAnimation2Map mySlide, myMapShape, WaferId
   
   Set AddMap = myMapShape ' ����ճ���� Shape ����
   On Error GoTo 0
End Function

' ���� PPT ��ҳ (�� 1 ��) �ı���͸�����
Private Function AddTitle2PPT(myPPT As Object, Lot)
   On Error Resume Next
   With myPPT.slides(1)
      If .Shapes.Count >= 1 Then .Shapes(1).TextFrame.TextRange.Text = Lot & " MAP Review"
      If .Shapes.Count >= 2 Then .Shapes(2).TextFrame.TextRange.Text = Application.UserName & vbCrLf & Format(Date, "yyyy-mm-dd")
   End With
   On Error GoTo 0
End Function

' Ϊ Bin Map �õ�Ƭ (�� 2 ��) ��ӱ���
Private Function AddBinMapSlide(myPPT As Object)
   On Error Resume Next
   Dim mySlide As Object: Set mySlide = myPPT.slides(2)
   If Not mySlide Is Nothing Then
       AddTitle mySlide, "Bin Map"
   End If
   On Error GoTo 0
End Function

' ��ָ���õ�Ƭ���һ����ǩ��Ϊ����
Private Function AddTitle(mySlide As Object, info As String)
   On Error Resume Next
   Dim myTitle As Object
   ' �����Ƿ��Ѵ��ڱ���ռλ��
   For Each myTitle In mySlide.Shapes
       If myTitle.Type = msoPlaceholder Then
           If myTitle.PlaceholderFormat.Type = ppPlaceholderTitle Or myTitle.PlaceholderFormat.Type = ppPlaceholderCenterTitle Then
               myTitle.TextFrame.TextRange.Text = info
               Exit Function ' �ҵ������ú��˳�
           End If
       End If
   Next
   ' ���û���ҵ�����ռλ���������һ���µı�ǩ
   Set myTitle = mySlide.Shapes.AddLabel(msoTextOrientationHorizontal, Left:=10, Top:=10, Width:=mySlide.Master.Width - 20, Height:=50)
   If Not myTitle Is Nothing Then
       myTitle.TextFrame.TextRange.Text = info
       myTitle.TextFrame.TextRange.Font.Size = 24 ' ���������С
       myTitle.TextFrame.TextRange.Font.Bold = msoTrue
   End If
   On Error GoTo 0
End Function

' (�˺����ƺ�δ������)
' ��ָ���õ�Ƭ���һ�� 5x5 �ı�񣬲�������� 1-25
Private Function AddWaferTable2Slide(mySlide As Object)
   Dim NumRows As Long: NumRows = 5
   Dim NumColumns As Long: NumColumns = 5
   Dim Left As Single: Left = 50
   Dim Top As Single: Top = 40
   Dim Width As Single: Width = 650
   Dim Height As Single: Height = 500
   
   On Error Resume Next
   Dim myTableShape As Object: Set myTableShape = mySlide.Shapes.AddTable(NumRows, NumColumns, Left, Top, Width, Height)
   If Err.Number <> 0 Or myTableShape Is Nothing Then
       gShow.ErrAlarm "�ڻõ�Ƭ " & mySlide.SlideIndex & " ��ӱ��ʧ�ܡ�"
       Exit Function
   End If
   
   With myTableShape.Table
      .FirstRow = False ' ������һ����Ϊ������
      .HorizBanding = False ' �ر�ˮƽ���Ƹ�ʽ
      Dim i As Long, j As Long
      For i = 1 To NumRows
         For j = 1 To NumColumns
            .Cell(i, j).Shape.TextFrame.TextRange.Text = (i - 1) * NumColumns + j
            .Cell(i, j).Shape.TextFrame.HorizontalAnchor = msoAnchorCenter
            .Cell(i, j).Shape.TextFrame.VerticalAnchor = msoAnchorMiddle
         Next
      Next
   End With
   On Error GoTo 0
End Function
