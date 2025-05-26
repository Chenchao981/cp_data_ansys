Attribute VB_Name = "�������Ͷ���"
Option Explicit

' ���嵥��������Ŀ������������Ϣ�ṹ
Public Type TestItem
   Id As String                  ' �ڲ�Ψһ��ʶ�� (���ܰ�����׺, �� "Param1", "Param12")
   Group As String               ' ����������ԭʼ����
   DisplayName As String         ' ������ʾ������
   Unit As String                ' ��λ
   ScopeHi As Variant            ' (��;����������Ϊ���㷶Χ����?)
   ScopeLow As Variant           ' (��;����������Ϊ���㷶Χ����?)
   SL As Variant                 ' ������� (Specification Lower Limit)
   SU As Variant                 ' ������� (Specification Upper Limit)
   QualityCharacteristic As String ' �������� (�� "��������", "��С����") - (��ǰ������δ��ʹ��)
   TestCond() As Variant         ' �������� (���飬�洢һ����������)
End Type

' ����ͳ�ƽ���Ľṹ (��ǰ�������ƺ�δʹ�ô������ṹ��Summary �н����㲿��)
Public Type StatResult
   N As Long                     ' ��������
   Avg As Double                 ' ƽ��ֵ
   s As Double                   ' ��׼�� (StdDev)
   Min As Double                 ' ��Сֵ
   Q1 As Double                  ' ��һ�ķ�λ��
   Q2 As Double                  ' ��λ�� (�ڶ��ķ�λ��)
   Q3 As Double                  ' �����ķ�λ��
   Max As Double                 ' ���ֵ
   VeryHiOutlier As Double       ' (��;����������Ϊ���쳣ֵ����)
   VeryLowOutlier As Double      ' (��;����������Ϊ���쳣ֵ����)
   OutlierHi As Double           ' (��;����������Ϊ����Ⱥֵ����)
   OutlierLow As Double          ' (��;����������Ϊ����Ⱥֵ����)
End Type

' ���嵥����Բ (Wafer) �����ݽṹ
Public Type CPWafer
   WaferId As String             ' ��Բ���
   SiteCount As Integer          ' (��;����������Ϊ���Ե�����)
   ChipCount As Long             ' �þ�Բ�ϵ�оƬ (���Ե�) ����
   ChipDatas() As Variant        ' �洢���в����������ݵĶ�ά���飬��һά�ǲ����������ڶ�ά��оƬ�����б� (��ʽ: Array(1 To ParamCount)(1 To ChipCount, 1 To 1))
   Seq() As Variant              ' оƬ����б� (��ʽ: Array(1 To ChipCount, 1 To 1))
   x() As Variant                ' оƬ X �����б� (��ʽ: Array(1 To ChipCount, 1 To 1))
   Y() As Variant                ' оƬ Y �����б� (��ʽ: Array(1 To ChipCount, 1 To 1))
   Bin() As Variant              ' оƬ Bin ֵ�б� (��ʽ: Array(1 To ChipCount, 1 To 1))
   MaxX As Integer               ' оƬ��� X ����
   MinX As Integer               ' оƬ��С X ����
   MaxY As Integer               ' оƬ��� Y ����
   MinY As Integer               ' оƬ��С Y ����
   Height As Integer             ' ��Բ�߶� (MaxY - MinY + 1)
   Width As Integer              ' ��Բ��� (MaxX - MinX + 1 �� + 2��ȡ���ڼ��㷽ʽ)
   ParamCount As Integer         ' �þ�Բ�����Ĳ�������
   Params() As TestItem          ' (�����ֶ�? ͨ���� CPLot ������) ������Ϣ����
   'ParamData() As Variant        ' (�����ֶ�? ChipDatas �Ѱ�������) ԭʼ��������
   StatInfo() As StatResult      ' (��ǰ������δ������ʹ��) ÿ��������ͳ����Ϣ
   PassBin As Variant            ' ����� Pass Bin ֵ
End Type

' �������� Lot �����ݽṹ
Public Type CPLot
   Id As String                  ' Lot ��� (��ǰ������δ������ʹ��)
   Product As String             ' ��Ʒ����
   WaferCount As Integer         ' Lot �а����ľ�Բ����
   Wafers() As CPWafer           ' �洢 Lot �����о�Բ���ݵ�����
   ParamCount As Integer         ' Lot ����Ĳ������� (���� Wafer Ӧһ��)
   Params() As TestItem          ' Lot ����Ĳ�����Ϣ���� (TestItem �ṹ)
   ParamData() As Variant        ' (��;�������������ڴ洢 Lot ����ľۺ�����)
   StatInfo() As StatResult      ' (��ǰ������δ������ʹ��) Lot ����Ĳ���ͳ����Ϣ
   PassBin As Variant            ' ����� Pass Bin ֵ (Ӧ�� CPWafer �е�һ��)
End Type
