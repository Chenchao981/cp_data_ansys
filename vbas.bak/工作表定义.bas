Attribute VB_Name = "��������"
Option Explicit

' --- ȫ�ֹ��������������� ---
' ��Щ�������ڷ����������Ŀ��ʹ�õ��ض�������

Public UI_SHEET As Worksheet             ' �û��������Ҫ�������ñ� (Sheet3)
Public SCOPE_SHEET As Worksheet          ' �������㷶Χ����� (Sheet4)
Public BIN_SETUP_SHEET As Worksheet      ' Bin ֵ��ɫ���ñ� (Sheet5)
Public XY_SETUP_SHEET As Worksheet       ' ɢ��ͼ (X-Y Plot) ���ú�ͼ��ģ��� (Sheet6)
Public BOXPLOT_SHEET As Worksheet      ' ����ͼ (Box Plot) ͼ��ģ��� (Sheet7)
Public FACTOR_SHEET As Worksheet       ' ����ˮƽ����� (���� Box Plot ����) (Sheet8)
Public DATA_COLOR_SHEET As Worksheet   ' ������ֵ��ɫͼ����ɫ�̶ȶ���� (Sheet9)
Public CAL_DATA_SETUP_SHEET As Worksheet ' �����������ݵ����ñ� (Sheet1)

' --- ȫ�ֹ��ܿ��ر�־�������� ---
' ��Щ�������ڴ洢�� UI_SHEET ��ȡ�Ĺ�������״̬

Public BOX_PLOT_FLAG As Boolean          ' �Ƿ���������ͼ
Public SCATTER_PLOT_FLAG As Boolean      ' �Ƿ�����ɢ��ͼ
Public BIN_MAP_PLOT_FLAG As Boolean      ' �Ƿ����� Bin Map ͼ
Public DATA_COLOR_PLOT_FLAG As Boolean   ' �Ƿ����ɲ�����ֵ��ɫͼ
Public INCLUDE_EXP_FACT_FLAG As Boolean  ' �Ƿ��� BoxPlot �а���ʵ��������Ϣ (���� FACTOR_SHEET)
Public ADD_CAL_DATA_FLAG As Boolean      ' �Ƿ�ִ�������������ݵĲ���

' ��ʼ�����̣��ں꿪ʼʱ���У���ȫ�ֹ��������ָ��ʵ�ʵĹ�������󣬲��� UI_SHEET ��ȡ���ܿ���״̬
Public Sub InitSheetSetup()
   
   On Error Resume Next ' ���Կ��ܵĴ��� (�繤�������ڻ����Ʋ�ƥ��)
   
   ' --- ���ù������������ ---
   ' ע�⣺����ֱ��ʹ���˹������ CodeName (Sheet1, Sheet3 ��)
   ' ���ַ�ʽ��ʹ�ù��������� (�� "UI") ����׳����Ϊ�û��޸Ĺ��������Ʋ���Ӱ�����
   Set CAL_DATA_SETUP_SHEET = Sheet1  ' Sheet1: "����������������"
   Set UI_SHEET = Sheet3              ' Sheet3: "UI"
   Set SCOPE_SHEET = Sheet4           ' Sheet4: "���㷶Χ����"
   Set BIN_SETUP_SHEET = Sheet5       ' Sheet5: "Bin��ɫ����"
   Set XY_SETUP_SHEET = Sheet6        ' Sheet6: "ɢ��ͼ����"
   Set BOXPLOT_SHEET = Sheet7         ' Sheet7: "BoxPlotͼģ��"
   Set FACTOR_SHEET = Sheet8          ' Sheet8: "Ƭ�������Ϣ"
   Set DATA_COLOR_SHEET = Sheet9      ' Sheet9: "��ֵ��ɫͼ����"
   
   ' ��� UI_SHEET �Ƿ�ɹ�����
   If UI_SHEET Is Nothing Then
       gShow.ErrStop "�޷��ҵ��û����湤���� (Sheet3: UI)�����鹤�����Ƿ���ڻ������Ƿ���ȷ��"
       Exit Sub
   End If
   
   ' --- �� UI_SHEET ��ȡ���ܿ���״̬ (ͨ�� CheckBox �ؼ�) ---
   With UI_SHEET
      ' ���� CheckBox �ؼ����ƹ̶�Ϊ CheckBox1, CheckBox2, ...
      BOX_PLOT_FLAG = (.CheckBoxes("Check Box 1").Value = xlOn) ' �Ƿ���������ͼ
      BIN_MAP_PLOT_FLAG = (.CheckBoxes("Check Box 2").Value = xlOn) ' �Ƿ����� Bin Map
      DATA_COLOR_PLOT_FLAG = (.CheckBoxes("Check Box 3").Value = xlOn) ' �Ƿ����ɲ�����ֵ��ɫͼ
      INCLUDE_EXP_FACT_FLAG = (.CheckBoxes("Check Box 4").Value = xlOn) ' Box Plot �Ƿ����������Ϣ
      SCATTER_PLOT_FLAG = (.CheckBoxes("Check Box 5").Value = xlOn) ' �Ƿ�����ɢ��ͼ
      ADD_CAL_DATA_FLAG = (.CheckBoxes("Check Box 6").Value = xlOn) ' �Ƿ����Ӽ�������
   End With
   
   On Error GoTo 0 ' �ָ�������
   
End Sub
