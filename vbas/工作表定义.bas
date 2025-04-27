Attribute VB_Name = "工作表定义"
Option Explicit

' --- 全局工作表对象变量定义 ---
' 这些变量用于方便地引用项目中使用的特定工作表

Public UI_SHEET As Worksheet             ' 用户界面和主要控制设置表 (Sheet3)
Public SCOPE_SHEET As Worksheet          ' 参数计算范围定义表 (Sheet4)
Public BIN_SETUP_SHEET As Worksheet      ' Bin 值颜色设置表 (Sheet5)
Public XY_SETUP_SHEET As Worksheet       ' 散点图 (X-Y Plot) 设置和图表模板表 (Sheet6)
Public BOXPLOT_SHEET As Worksheet      ' 箱线图 (Box Plot) 图表模板表 (Sheet7)
Public FACTOR_SHEET As Worksheet       ' 因子水平定义表 (用于 Box Plot 分组) (Sheet8)
Public DATA_COLOR_SHEET As Worksheet   ' 参数数值颜色图的颜色刻度定义表 (Sheet9)
Public CAL_DATA_SETUP_SHEET As Worksheet ' 增加运算数据的设置表 (Sheet1)

' --- 全局功能开关标志变量定义 ---
' 这些变量用于存储从 UI_SHEET 读取的功能启用状态

Public BOX_PLOT_FLAG As Boolean          ' 是否生成箱线图
Public SCATTER_PLOT_FLAG As Boolean      ' 是否生成散点图
Public BIN_MAP_PLOT_FLAG As Boolean      ' 是否生成 Bin Map 图
Public DATA_COLOR_PLOT_FLAG As Boolean   ' 是否生成参数数值颜色图
Public INCLUDE_EXP_FACT_FLAG As Boolean  ' 是否在 BoxPlot 中包含实验因子信息 (来自 FACTOR_SHEET)
Public ADD_CAL_DATA_FLAG As Boolean      ' 是否执行增加运算数据的步骤

' 初始化过程：在宏开始时运行，将全局工作表变量指向实际的工作表对象，并从 UI_SHEET 读取功能开关状态
Public Sub InitSheetSetup()
   
   On Error Resume Next ' 忽略可能的错误 (如工作表不存在或名称不匹配)
   
   ' --- 设置工作表对象引用 ---
   ' 注意：这里直接使用了工作表的 CodeName (Sheet1, Sheet3 等)
   ' 这种方式比使用工作表名称 (如 "UI") 更健壮，因为用户修改工作表名称不会影响代码
   Set CAL_DATA_SETUP_SHEET = Sheet1  ' Sheet1: "增加运算数据设置"
   Set UI_SHEET = Sheet3              ' Sheet3: "UI"
   Set SCOPE_SHEET = Sheet4           ' Sheet4: "计算范围定义"
   Set BIN_SETUP_SHEET = Sheet5       ' Sheet5: "Bin颜色设置"
   Set XY_SETUP_SHEET = Sheet6        ' Sheet6: "散点图设置"
   Set BOXPLOT_SHEET = Sheet7         ' Sheet7: "BoxPlot图模板"
   Set FACTOR_SHEET = Sheet8          ' Sheet8: "片号相关信息"
   Set DATA_COLOR_SHEET = Sheet9      ' Sheet9: "数值颜色图设置"
   
   ' 检查 UI_SHEET 是否成功设置
   If UI_SHEET Is Nothing Then
       gShow.ErrStop "无法找到用户界面工作表 (Sheet3: UI)。请检查工作表是否存在或名称是否正确。"
       Exit Sub
   End If
   
   ' --- 从 UI_SHEET 读取功能开关状态 (通过 CheckBox 控件) ---
   With UI_SHEET
      ' 假设 CheckBox 控件名称固定为 CheckBox1, CheckBox2, ...
      BOX_PLOT_FLAG = (.CheckBoxes("Check Box 1").Value = xlOn) ' 是否生成箱线图
      BIN_MAP_PLOT_FLAG = (.CheckBoxes("Check Box 2").Value = xlOn) ' 是否生成 Bin Map
      DATA_COLOR_PLOT_FLAG = (.CheckBoxes("Check Box 3").Value = xlOn) ' 是否生成参数数值颜色图
      INCLUDE_EXP_FACT_FLAG = (.CheckBoxes("Check Box 4").Value = xlOn) ' Box Plot 是否包含因子信息
      SCATTER_PLOT_FLAG = (.CheckBoxes("Check Box 5").Value = xlOn) ' 是否生成散点图
      ADD_CAL_DATA_FLAG = (.CheckBoxes("Check Box 6").Value = xlOn) ' 是否增加计算数据
   End With
   
   On Error GoTo 0 ' 恢复错误处理
   
End Sub
