Attribute VB_Name = "数据类型定义"
Option Explicit

' 定义单个测试项目（参数）的信息结构
Public Type TestItem
   Id As String                  ' 内部唯一标识符 (可能包含后缀, 如 "Param1", "Param12")
   Group As String               ' 参数的组别或原始名称
   DisplayName As String         ' 用于显示的名称
   Unit As String                ' 单位
   ScopeHi As Variant            ' (用途不明，可能为计算范围上限?)
   ScopeLow As Variant           ' (用途不明，可能为计算范围下限?)
   SL As Variant                 ' 规格下限 (Specification Lower Limit)
   SU As Variant                 ' 规格上限 (Specification Upper Limit)
   QualityCharacteristic As String ' 质量特性 (如 "望大特性", "望小特性") - (当前代码中未见使用)
   TestCond() As Variant         ' 测试条件 (数组，存储一个或多个条件)
End Type

' 定义统计结果的结构 (当前代码中似乎未使用此完整结构，Summary 中仅计算部分)
Public Type StatResult
   N As Long                     ' 样本数量
   Avg As Double                 ' 平均值
   s As Double                   ' 标准差 (StdDev)
   Min As Double                 ' 最小值
   Q1 As Double                  ' 第一四分位数
   Q2 As Double                  ' 中位数 (第二四分位数)
   Q3 As Double                  ' 第三四分位数
   Max As Double                 ' 最大值
   VeryHiOutlier As Double       ' (用途不明，可能为高异常值界限)
   VeryLowOutlier As Double      ' (用途不明，可能为低异常值界限)
   OutlierHi As Double           ' (用途不明，可能为高离群值界限)
   OutlierLow As Double          ' (用途不明，可能为低离群值界限)
End Type

' 定义单个晶圆 (Wafer) 的数据结构
Public Type CPWafer
   WaferId As String             ' 晶圆编号
   SiteCount As Integer          ' (用途不明，可能为测试点数量)
   ChipCount As Long             ' 该晶圆上的芯片 (测试点) 总数
   ChipDatas() As Variant        ' 存储所有参数测试数据的二维数组，第一维是参数索引，第二维是芯片数据列表 (格式: Array(1 To ParamCount)(1 To ChipCount, 1 To 1))
   Seq() As Variant              ' 芯片序号列表 (格式: Array(1 To ChipCount, 1 To 1))
   x() As Variant                ' 芯片 X 坐标列表 (格式: Array(1 To ChipCount, 1 To 1))
   Y() As Variant                ' 芯片 Y 坐标列表 (格式: Array(1 To ChipCount, 1 To 1))
   Bin() As Variant              ' 芯片 Bin 值列表 (格式: Array(1 To ChipCount, 1 To 1))
   MaxX As Integer               ' 芯片最大 X 坐标
   MinX As Integer               ' 芯片最小 X 坐标
   MaxY As Integer               ' 芯片最大 Y 坐标
   MinY As Integer               ' 芯片最小 Y 坐标
   Height As Integer             ' 晶圆高度 (MaxY - MinY + 1)
   Width As Integer              ' 晶圆宽度 (MaxX - MinX + 1 或 + 2，取决于计算方式)
   ParamCount As Integer         ' 该晶圆包含的参数数量
   Params() As TestItem          ' (冗余字段? 通常在 CPLot 级别定义) 参数信息数组
   'ParamData() As Variant        ' (冗余字段? ChipDatas 已包含数据) 原始参数数据
   StatInfo() As StatResult      ' (当前代码中未见填充和使用) 每个参数的统计信息
   PassBin As Variant            ' 定义的 Pass Bin 值
End Type

' 定义整个 Lot 的数据结构
Public Type CPLot
   Id As String                  ' Lot 编号 (当前代码中未见填充和使用)
   Product As String             ' 产品名称
   WaferCount As Integer         ' Lot 中包含的晶圆数量
   Wafers() As CPWafer           ' 存储 Lot 中所有晶圆数据的数组
   ParamCount As Integer         ' Lot 级别的参数数量 (所有 Wafer 应一致)
   Params() As TestItem          ' Lot 级别的参数信息数组 (TestItem 结构)
   ParamData() As Variant        ' (用途不明，可能用于存储 Lot 级别的聚合数据)
   StatInfo() As StatResult      ' (当前代码中未见填充和使用) Lot 级别的参数统计信息
   PassBin As Variant            ' 定义的 Pass Bin 值 (应与 CPWafer 中的一致)
End Type
