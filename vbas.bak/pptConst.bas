Attribute VB_Name = "pptConst"
' PowerPoint 常量定义模块
' 此模块包含 PowerPoint 对象模型中使用的各种常量值
' 用于在 VBA 中与 PowerPoint 对象进行交互

' 窗口状态常量
Public Const ppWindowNormal As Integer = 1       ' 正常窗口
Public Const ppWindowMinimized As Integer = 2    ' 最小化窗口
Public Const ppWindowMaximized As Integer = 3    ' 最大化窗口
Public Const ppArrangeTiled As Integer = 1       ' 平铺排列
Public Const ppArrangeCascade As Integer = 2     ' 层叠排列

' 视图类型常量
Public Const ppViewSlide As Integer = 1          ' 幻灯片视图
Public Const ppViewSlideMaster As Integer = 2    ' 幻灯片母版视图
Public Const ppViewNotesPage As Integer = 3      ' 备注页视图
Public Const ppViewHandoutMaster As Integer = 4  ' 讲义母版视图
Public Const ppViewNotesMaster As Integer = 5    ' 备注母版视图
Public Const ppViewOutline As Integer = 6        ' 大纲视图
Public Const ppViewSlideSorter As Integer = 7    ' 幻灯片浏览视图
Public Const ppViewTitleMaster As Integer = 8    ' 标题母版视图
Public Const ppViewNormal As Integer = 9         ' 普通视图
Public Const ppViewPrintPreview As Integer = 10  ' 打印预览视图
Public Const ppViewThumbnails As Integer = 11    ' 缩略图视图
Public Const ppViewMasterThumbnails As Integer = 12 ' 母版缩略图视图

' 配色方案常量
Public Const ppSchemeColorMixed As Integer = -2  ' 混合方案颜色
Public Const ppNotSchemeColor As Integer = 0     ' 非方案颜色
Public Const ppBackground As Integer = 1         ' 背景色
Public Const ppForeground As Integer = 2         ' 前景色
Public Const ppShadow As Integer = 3             ' 阴影色
Public Const ppTitle As Integer = 4              ' 标题色
Public Const ppFill As Integer = 5               ' 填充色
Public Const ppAccent1 As Integer = 6            ' 强调色1
Public Const ppAccent2 As Integer = 7            ' 强调色2
Public Const ppAccent3 As Integer = 8            ' 强调色3

' 幻灯片尺寸常量
Public Const ppSlideSizeOnScreen As Integer = 1         ' 屏幕显示尺寸
Public Const ppSlideSizeLetterPaper As Integer = 2      ' 信纸尺寸
Public Const ppSlideSizeA4Paper As Integer = 3          ' A4纸尺寸
Public Const ppSlideSize35MM As Integer = 4             ' 35毫米幻灯片尺寸
Public Const ppSlideSizeOverhead As Integer = 5         ' 投影片尺寸
Public Const ppSlideSizeBanner As Integer = 6           ' 横幅尺寸
Public Const ppSlideSizeCustom As Integer = 7           ' 自定义尺寸
Public Const ppSlideSizeLedgerPaper As Integer = 8      ' 帐簿纸尺寸
Public Const ppSlideSizeA3Paper As Integer = 9          ' A3纸尺寸
Public Const ppSlideSizeB4ISOPaper As Integer = 10      ' B4 ISO纸尺寸
Public Const ppSlideSizeB5ISOPaper As Integer = 11      ' B5 ISO纸尺寸
Public Const ppSlideSizeB4JISPaper As Integer = 12      ' B4 JIS纸尺寸
Public Const ppSlideSizeB5JISPaper As Integer = 13      ' B5 JIS纸尺寸
Public Const ppSlideSizeHagakiCard As Integer = 14      ' 明信片尺寸

' 保存格式常量
Public Const ppSaveAsPresentation As Integer = 1        ' 保存为演示文稿
Public Const ppSaveAsPowerPoint7 As Integer = 2         ' 保存为PowerPoint 7格式
Public Const ppSaveAsPowerPoint4 As Integer = 3         ' 保存为PowerPoint 4格式
Public Const ppSaveAsPowerPoint3 As Integer = 4         ' 保存为PowerPoint 3格式
Public Const ppSaveAsTemplate As Integer = 5            ' 保存为模板
Public Const ppSaveAsRTF As Integer = 6                 ' 保存为RTF
Public Const ppSaveAsShow As Integer = 7                ' 保存为幻灯片放映
Public Const ppSaveAsAddIn As Integer = 8               ' 保存为加载项
Public Const ppSaveAsPowerPoint4FarEast As Integer = 10 ' 保存为PowerPoint 4远东版格式
Public Const ppSaveAsDefault As Integer = 11            ' 保存为默认格式
Public Const ppSaveAsHTML As Integer = 12               ' 保存为HTML
Public Const ppSaveAsHTMLv3 As Integer = 13             ' 保存为HTML v3
Public Const ppSaveAsHTMLDual As Integer = 14           ' 保存为双语HTML
Public Const ppSaveAsMetaFile As Integer = 15           ' 保存为图元文件
Public Const ppSaveAsGIF As Integer = 16                ' 保存为GIF
Public Const ppSaveAsJPG As Integer = 17                ' 保存为JPG
Public Const ppSaveAsPNG As Integer = 18                ' 保存为PNG
Public Const ppSaveAsBMP As Integer = 19                ' 保存为BMP
Public Const ppSaveAsWebArchive As Integer = 20         ' 保存为Web存档
Public Const ppSaveAsTIF As Integer = 21                ' 保存为TIF
Public Const ppSaveAsPresForReview As Integer = 22      ' 保存为审阅用演示文稿
Public Const ppSaveAsEMF As Integer = 23                ' 保存为EMF

' 文本样式常量
Public Const ppDefaultStyle As Integer = 1              ' 默认样式
Public Const ppTitleStyle As Integer = 2                ' 标题样式
Public Const ppBodyStyle As Integer = 3                 ' 正文样式

' 幻灯片布局常量
Public Const ppLayoutMixed As Integer = -2              ' 混合布局
Public Const ppLayoutTitle As Integer = 1               ' 标题布局
Public Const ppLayoutText As Integer = 2                ' 文本布局
Public Const ppLayoutTwoColumnText As Integer = 3       ' 两栏文本布局
Public Const ppLayoutTable As Integer = 4               ' 表格布局
Public Const ppLayoutTextAndChart As Integer = 5        ' 文本和图表布局
Public Const ppLayoutChartAndText As Integer = 6        ' 图表和文本布局
Public Const ppLayoutOrgchart As Integer = 7            ' 组织结构图布局
Public Const ppLayoutChart As Integer = 8               ' 图表布局
Public Const ppLayoutTextAndClipart As Integer = 9      ' 文本和剪贴画布局
Public Const ppLayoutClipartAndText As Integer = 10     ' 剪贴画和文本布局
Public Const ppLayoutTitleOnly As Integer = 11          ' 仅标题布局
Public Const ppLayoutBlank As Integer = 12              ' 空白布局
Public Const ppLayoutTextAndObject As Integer = 13      ' 文本和对象布局
Public Const ppLayoutObjectAndText As Integer = 14      ' 对象和文本布局
Public Const ppLayoutLargeObject As Integer = 15        ' 大对象布局
Public Const ppLayoutObject As Integer = 16             ' 对象布局
Public Const ppLayoutTextAndMediaClip As Integer = 17   ' 文本和媒体剪辑布局
Public Const ppLayoutMediaClipAndText As Integer = 18   ' 媒体剪辑和文本布局
Public Const ppLayoutObjectOverText As Integer = 19     ' 对象在文本上布局
Public Const ppLayoutTextOverObject As Integer = 20     ' 文本在对象上布局
Public Const ppLayoutTextAndTwoObjects As Integer = 21  ' 文本和两个对象布局
Public Const ppLayoutTwoObjectsAndText As Integer = 22  ' 两个对象和文本布局
Public Const ppLayoutTwoObjectsOverText As Integer = 23 ' 两个对象在文本上布局
Public Const ppLayoutFourObjects As Integer = 24        ' 四个对象布局
Public Const ppLayoutVerticalText As Integer = 25       ' 垂直文本布局
Public Const ppLayoutClipArtAndVerticalText As Integer = 26 ' 剪贴画和垂直文本布局
Public Const ppLayoutVerticalTitleAndText As Integer = 27    ' 垂直标题和文本布局
Public Const ppLayoutVerticalTitleAndTextOverChart As Integer = 28 ' 垂直标题和文本在图表上布局
Public Const ppLayoutTwoObjects As Integer = 29         ' 两个对象布局
Public Const ppLayoutObjectAndTwoObjects As Integer = 30 ' 一个对象和两个对象布局
Public Const ppLayoutTwoObjectsAndObject As Integer = 31 ' 两个对象和一个对象布局

' 幻灯片切换特效常量
Public Const ppEffectMixed As Integer = -2            ' 混合特效
Public Const ppEffectNone As Integer = 0              ' 无特效
Public Const ppEffectCut As Integer = 257             ' 剪切
Public Const ppEffectCutThroughBlack As Integer = 258 ' 通过黑色剪切
Public Const ppEffectRandom As Integer = 513          ' 随机
Public Const ppEffectBlindsHorizontal As Integer = 769 ' 水平百叶窗
Public Const ppEffectBlindsVertical As Integer = 770   ' 垂直百叶窗
Public Const ppEffectCheckerboardAcross As Integer = 1025 ' 横向棋盘
Public Const ppEffectCheckerboardDown As Integer = 1026   ' 纵向棋盘
Public Const ppEffectCoverLeft As Integer = 1281      ' 从左覆盖
Public Const ppEffectCoverUp As Integer = 1282        ' 从上覆盖
Public Const ppEffectCoverRight As Integer = 1283     ' 从右覆盖
Public Const ppEffectCoverDown As Integer = 1284      ' 从下覆盖
Public Const ppEffectCoverLeftUp As Integer = 1285    ' 从左上覆盖
Public Const ppEffectCoverRightUp As Integer = 1286   ' 从右上覆盖
Public Const ppEffectCoverLeftDown As Integer = 1287  ' 从左下覆盖
Public Const ppEffectCoverRightDown As Integer = 1288 ' 从右下覆盖
Public Const ppEffectDissolve As Integer = 1537       ' 溶解
Public Const ppEffectFade As Integer = 1793           ' 淡入淡出
Public Const ppEffectUncoverLeft As Integer = 2049    ' 从左展开
Public Const ppEffectUncoverUp As Integer = 2050      ' 从上展开
Public Const ppEffectUncoverRight As Integer = 2051   ' 从右展开
Public Const ppEffectUncoverDown As Integer = 2052    ' 从下展开
Public Const ppEffectUncoverLeftUp As Integer = 2053  ' 从左上展开
Public Const ppEffectUncoverRightUp As Integer = 2054 ' 从右上展开
Public Const ppEffectUncoverLeftDown As Integer = 2055 ' 从左下展开
Public Const ppEffectUncoverRightDown As Integer = 2056 ' 从右下展开
Public Const ppEffectRandomBarsHorizontal As Integer = 2305 ' 随机水平条
Public Const ppEffectRandomBarsVertical As Integer = 2306   ' 随机垂直条
Public Const ppEffectStripsUpLeft As Integer = 2561   ' 左上条纹
Public Const ppEffectStripsUpRight As Integer = 2562  ' 右上条纹
Public Const ppEffectStripsDownLeft As Integer = 2563 ' 左下条纹
Public Const ppEffectStripsDownRight As Integer = 2564 ' 右下条纹
Public Const ppEffectStripsLeftUp As Integer = 2565   ' 左上条纹
Public Const ppEffectStripsRightUp As Integer = 2566  ' 右上条纹
Public Const ppEffectStripsLeftDown As Integer = 2567 ' 左下条纹
Public Const ppEffectStripsRightDown As Integer = 2568 ' 右下条纹
Public Const ppEffectWipeLeft As Integer = 2817      ' 从左擦除
Public Const ppEffectWipeUp As Integer = 2818        ' 从上擦除
Public Const ppEffectWipeRight As Integer = 2819     ' 从右擦除
Public Const ppEffectWipeDown As Integer = 2820      ' 从下擦除
Public Const ppEffectBoxOut As Integer = 3073        ' 向外扩展
Public Const ppEffectBoxIn As Integer = 3074         ' 向内收缩

' 动画级别常量
Public Const ppAnimateLevelMixed As Integer = -2       ' 混合级别
Public Const ppAnimateLevelNone As Integer = 0         ' 无动画
Public Const ppAnimateByFirstLevel As Integer = 1      ' 第一级
Public Const ppAnimateBySecondLevel As Integer = 2     ' 第二级
Public Const ppAnimateByThirdLevel As Integer = 3      ' 第三级
Public Const ppAnimateByFourthLevel As Integer = 4     ' 第四级
Public Const ppAnimateByFifthLevel As Integer = 5      ' 第五级
Public Const ppAnimateByAllLevels As Integer = 16      ' 所有级别

' 动画单位常量
Public Const ppAnimateUnitMixed As Integer = -2        ' 混合单位
Public Const ppAnimateByParagraph As Integer = 0       ' 按段落
Public Const ppAnimateByWord As Integer = 1            ' 按词
Public Const ppAnimateByCharacter As Integer = 2       ' 按字符

' 图表动画常量
Public Const ppAnimateChartMixed As Integer = -2             ' 混合图表动画
Public Const ppAnimateBySeries As Integer = 1                ' 按系列
Public Const ppAnimateByCategory As Integer = 2              ' 按类别
Public Const ppAnimateBySeriesElements As Integer = 3        ' 按系列元素
Public Const ppAnimateByCategoryElements As Integer = 4      ' 按类别元素
Public Const ppAnimateChartAllAtOnce As Integer = 5          ' 整体显示

' 后续效果常量
Public Const ppAfterEffectMixed As Integer = -2              ' 混合后效果
Public Const ppAfterEffectNothing As Integer = 0             ' 无效果
Public Const ppAfterEffectHide As Integer = 1                ' 隐藏
Public Const ppAfterEffectDim As Integer = 2                 ' 淡化
Public Const ppAfterEffectHideOnClick As Integer = 3         ' 单击后隐藏

' 进度模式常量
Public Const ppAdvanceModeMixed As Integer = -2              ' 混合模式
Public Const ppAdvanceOnClick As Integer = 1                 ' 单击时前进
Public Const ppAdvanceOnTime As Integer = 2                  ' 定时前进

' 声音效果常量
Public Const ppSoundEffectsMixed As Integer = -2             ' 混合声音效果
Public Const ppSoundNone As Integer = 0                      ' 无声音
Public Const ppSoundStopPrevious As Integer = 1              ' 停止前一个声音
Public Const ppSoundFile As Integer = 2                      ' 声音文件

' 颜色跟随常量
Public Const ppFollowColorsMixed As Integer = -2             ' 混合颜色跟随
Public Const ppFollowColorsNone As Integer = 0               ' 不跟随颜色
Public Const ppFollowColorsScheme As Integer = 1             ' 跟随方案颜色
Public Const ppFollowColorsTextAndBackground As Integer = 2  ' 跟随文本和背景颜色

' 更新选项常量
Public Const ppUpdateOptionMixed As Integer = -2             ' 混合更新选项
Public Const ppUpdateOptionManual As Integer = 1             ' 手动更新
Public Const ppUpdateOptionAutomatic As Integer = 2          ' 自动更新

' 对齐方式常量
Public Const ppAlignmentMixed As Integer = -2                ' 混合对齐
Public Const ppAlignLeft As Integer = 1                      ' 左对齐
Public Const ppAlignCenter As Integer = 2                    ' 居中对齐
Public Const ppAlignRight As Integer = 3                     ' 右对齐
Public Const ppAlignJustify As Integer = 4                   ' 两端对齐
Public Const ppAlignDistribute As Integer = 5                ' 分散对齐
Public Const ppAlignThaiDistribute As Integer = 6            ' 泰文分散对齐
Public Const ppAlignJustifyLow As Integer = 7                ' 低位两端对齐

' 幻灯片放映鼠标指针常量
Public Const ppSlideShowPointerNone As Integer = 0           ' 无指针
Public Const ppSlideShowPointerArrow As Integer = 1          ' 箭头指针
Public Const ppSlideShowPointerPen As Integer = 2            ' 笔指针
Public Const ppSlideShowPointerAlwaysHidden As Integer = 3   ' 总是隐藏
Public Const ppSlideShowPointerAutoArrow As Integer = 4      ' 自动箭头

' 幻灯片放映状态常量
Public Const ppSlideShowRunning As Integer = 1               ' 正在运行
Public Const ppSlideShowPaused As Integer = 2                ' 已暂停
Public Const ppSlideShowBlackScreen As Integer = 3           ' 黑屏
Public Const ppSlideShowWhiteScreen As Integer = 4           ' 白屏
Public Const ppSlideShowDone As Integer = 5                  ' 已完成

' 幻灯片放映前进方式常量
Public Const ppSlideShowManualAdvance As Integer = 1         ' 手动前进
Public Const ppSlideShowUseSlideTimings As Integer = 2       ' 使用幻灯片计时
Public Const ppSlideShowRehearseNewTimings As Integer = 3    ' 排练新计时

' 文件对话框常量
Public Const ppFileDialogOpen As Integer = 1                 ' 打开对话框
Public Const ppFileDialogSave As Integer = 2                 ' 保存对话框

' 打印输出常量
Public Const ppPrintOutputSlides As Integer = 1              ' 打印幻灯片
Public Const ppPrintOutputTwoSlideHandouts As Integer = 2    ' 两张幻灯片讲义
Public Const ppPrintOutputThreeSlideHandouts As Integer = 3  ' 三张幻灯片讲义
Public Const ppPrintOutputSixSlideHandouts As Integer = 4    ' 六张幻灯片讲义
Public Const ppPrintOutputNotesPages As Integer = 5          ' 打印备注页
Public Const ppPrintOutputOutline As Integer = 6             ' 打印大纲
Public Const ppPrintOutputBuildSlides As Integer = 7         ' 打印构建幻灯片
Public Const ppPrintOutputFourSlideHandouts As Integer = 8   ' 四张幻灯片讲义
Public Const ppPrintOutputNineSlideHandouts As Integer = 9   ' 九张幻灯片讲义
Public Const ppPrintOutputOneSlideHandouts As Integer = 10   ' 一张幻灯片讲义

' 打印顺序常量
Public Const ppPrintHandoutVerticalFirst As Integer = 1      ' 先垂直再水平
Public Const ppPrintHandoutHorizontalFirst As Integer = 2    ' 先水平再垂直

' 打印颜色常量
Public Const ppPrintColor As Integer = 1                     ' 彩色打印
Public Const ppPrintBlackAndWhite As Integer = 2             ' 黑白打印
Public Const ppPrintPureBlackAndWhite As Integer = 3         ' 纯黑白打印

' 选择类型常量
Public Const ppSelectionNone As Integer = 0                  ' 无选择
Public Const ppSelectionSlides As Integer = 1                ' 幻灯片选择
Public Const ppSelectionShapes As Integer = 2                ' 形状选择
Public Const ppSelectionText As Integer = 3                  ' 文本选择

' 文本方向常量
Public Const ppDirectionMixed As Integer = -2                ' 混合方向
Public Const ppDirectionLeftToRight As Integer = 1           ' 从左到右
Public Const ppDirectionRightToLeft As Integer = 2           ' 从右到左

' 日期时间格式常量
Public Const ppDateTimeFormatMixed As Integer = -2           ' 混合日期时间格式
Public Const ppDateTimeMdyy As Integer = 1                   ' 月/日/年
Public Const ppDateTimeddddMMMMddyyyy As Integer = 2         ' 星期几, 月 日, 年
Public Const ppDateTimedMMMMyyyy As Integer = 3              ' 日 月 年
Public Const ppDateTimeMMMMdyyyy As Integer = 4              ' 月 日, 年
Public Const ppDateTimedMMMyy As Integer = 5                 ' 日 月 年
Public Const ppDateTimeMMMMyy As Integer = 6                 ' 月 年
Public Const ppDateTimeMMyy As Integer = 7                   ' 月/年
Public Const ppDateTimeMMddyyHmm As Integer = 8              ' 月/日/年 时:分
Public Const ppDateTimeMMddyyhmmAMPM As Integer = 9          ' 月/日/年 时:分 AM/PM

' 幻灯片切换速度常量
Public Const ppTransitionSpeedMixed As Integer = -2          ' 混合速度
Public Const ppTransitionSpeedSlow As Integer = 1            ' 慢速
Public Const ppTransitionSpeedMedium As Integer = 2          ' 中速
Public Const ppTransitionSpeedFast As Integer = 3            ' 快速

' 鼠标事件常量
Public Const ppMouseClick As Integer = 1                     ' 鼠标点击
Public Const ppMouseOver As Integer = 2                      ' 鼠标悬停

' 动作类型常量
Public Const ppActionMixed As Integer = -2                   ' 混合动作
Public Const ppActionNone As Integer = 0                     ' 无动作
Public Const ppActionNextSlide As Integer = 1                ' 下一张幻灯片
Public Const ppActionPreviousSlide As Integer = 2            ' 上一张幻灯片
Public Const ppActionFirstSlide As Integer = 3               ' 第一张幻灯片
Public Const ppActionLastSlide As Integer = 4                ' 最后一张幻灯片
Public Const ppActionLastSlideViewed As Integer = 5          ' 上次查看的幻灯片
Public Const ppActionEndShow As Integer = 6                  ' 结束放映
Public Const ppActionHyperlink As Integer = 7                ' 超链接
Public Const ppActionRunMacro As Integer = 8                 ' 运行宏
Public Const ppActionRunProgram As Integer = 9               ' 运行程序

' 占位符类型常量
Public Const ppPlaceholderMixed As Integer = -2              ' 混合占位符
Public Const ppPlaceholderTitle As Integer = 1               ' 标题占位符
Public Const ppPlaceholderBody As Integer = 2                ' 正文占位符
Public Const ppPlaceholderCenterTitle As Integer = 3         ' 居中标题占位符
Public Const ppPlaceholderSubtitle As Integer = 4            ' 副标题占位符
Public Const ppPlaceholderVerticalTitle As Integer = 5       ' 垂直标题占位符
Public Const ppPlaceholderVerticalBody As Integer = 6        ' 垂直正文占位符
Public Const ppPlaceholderObject As Integer = 7              ' 对象占位符
Public Const ppPlaceholderChart As Integer = 8               ' 图表占位符
Public Const ppPlaceholderBitmap As Integer = 9              ' 位图占位符
Public Const ppPlaceholderMediaClip As Integer = 10          ' 媒体剪辑占位符
Public Const ppPlaceholderOrgChart As Integer = 11           ' 组织结构图占位符
Public Const ppPlaceholderTable As Integer = 12              ' 表格占位符
Public Const ppPlaceholderSlideNumber As Integer = 13        ' 幻灯片编号占位符
Public Const ppPlaceholderHeader As Integer = 14             ' 页眉占位符
Public Const ppPlaceholderFooter As Integer = 15             ' 页脚占位符
Public Const ppPlaceholderDate As Integer = 16               ' 日期占位符

' 放映类型常量
Public Const ppShowTypeSpeaker As Integer = 1                ' 演讲者放映
Public Const ppShowTypeWindow As Integer = 2                 ' 窗口放映
Public Const ppShowTypeKiosk As Integer = 3                  ' 自动循环放映

' 打印范围常量
Public Const ppPrintAll As Integer = 1                       ' 打印全部
Public Const ppPrintSelection As Integer = 2                 ' 打印选择内容
Public Const ppPrintCurrent As Integer = 3                   ' 打印当前幻灯片
Public Const ppPrintSlideRange As Integer = 4                ' 打印幻灯片范围
Public Const ppPrintNamedSlideShow As Integer = 5            ' 打印命名幻灯片放映

' 更多PowerPoint常量...
' 下面是一些其他常用的PowerPoint常量

' OLE对象动词常量
Public Const ppOLEVerbOpen As Integer = &H1         ' 打开OLE对象
Public Const ppOLEVerbPrimary As Integer = &H0      ' 主要OLE动词

' 文本组合方式常量
Public Const ppBodyStyleMixed As Integer = -2       ' 混合正文样式
Public Const ppBodyStyleLevel1 As Integer = 1       ' 一级正文样式
Public Const ppBodyStyleLevel2 As Integer = 2       ' 二级正文样式
Public Const ppBodyStyleLevel3 As Integer = 3       ' 三级正文样式
Public Const ppBodyStyleLevel4 As Integer = 4       ' 四级正文样式

' 标尺单位常量
Public Const ppRulerInches As Integer = 0           ' 英寸
Public Const ppRulerPoints As Integer = 1           ' 磅
Public Const ppRulerCentimeters As Integer = 2      ' 厘米
Public Const ppRulerPicas As Integer = 3            ' Pica
Public Const ppRulerMillimeters As Integer = 4      ' 毫米

' 标尺方向常量
Public Const ppTabStopLeft As Integer = 1           ' 左对齐制表位
Public Const ppTabStopCenter As Integer = 2         ' 居中制表位
Public Const ppTabStopRight As Integer = 3          ' 右对齐制表位
Public Const ppTabStopDecimal As Integer = 4        ' 小数点对齐制表位

' 自动适应文本常量
Public Const ppAutoSizeNone As Integer = 0          ' 不自动调整大小
Public Const ppAutoSizeShapeToFitText As Integer = 1 ' 调整形状以适应文本
Public Const ppAutoSizeTextToFitShape As Integer = 2 ' 调整文本以适应形状

' 声音格式常量
Public Const ppSoundFormatMixed As Integer = -2     ' 混合声音格式
Public Const ppSoundFormatNone As Integer = 0       ' 无声音格式
Public Const ppSoundFormatWAV As Integer = 1        ' WAV格式
Public Const ppSoundFormatMIDI As Integer = 2       ' MIDI格式
Public Const ppSoundFormatCDAudio As Integer = 3    ' CD音频格式

' 媒体类型常量
Public Const ppMediaTypeMixed As Integer = -2       ' 混合媒体类型
Public Const ppMediaTypeOther As Integer = 1        ' 其他媒体类型
Public Const ppMediaTypeSound As Integer = 2        ' 声音媒体类型
Public Const ppMediaTypeMovie As Integer = 3        ' 电影媒体类型

' 纸张大小常量
Public Const ppPaperSize10x14 As Integer = 0        ' 10x14英寸
Public Const ppPaperSize11x17 As Integer = 1        ' 11x17英寸
Public Const ppPaperSizeA3 As Integer = 2           ' A3纸
Public Const ppPaperSizeA4 As Integer = 3           ' A4纸
Public Const ppPaperSizeA5 As Integer = 4           ' A5纸
Public Const ppPaperSizeB4 As Integer = 5           ' B4纸
Public Const ppPaperSizeB5 As Integer = 6           ' B5纸
Public Const ppPaperSizeLetter As Integer = 7       ' 信纸大小
Public Const ppPaperSizeLegal As Integer = 8        ' 法律文书大小

' 超链接类型常量
Public Const ppHyperlinkTypeURL As Integer = 0      ' URL超链接
Public Const ppHyperlinkTypeFile As Integer = 1     ' 文件超链接
Public Const ppHyperlinkTypeSlide As Integer = 2    ' 幻灯片超链接

' 放映类型常量
Public Const ppShowTypeManual As Integer = 1        ' 手动放映
Public Const ppShowTypeAutomatic As Integer = 2     ' 自动放映
Public Const ppShowTypeBrowse As Integer = 3        ' 浏览模式放映

' 媒体控制样式常量
Public Const ppMediaControlsClassic As Integer = 0  ' 经典控制样式
Public Const ppMediaControlsSlim As Integer = 1     ' 精简控制样式
Public Const ppMediaControlsNone As Integer = 2     ' 无控制样式

' 媒体播放模式常量
Public Const ppMediaPlayModeOnce As Integer = 0     ' 播放一次
Public Const ppMediaPlayModeLoop As Integer = 1     ' 循环播放
Public Const ppMediaPlayModeContinuous As Integer = 2 ' 连续播放

' 结尾常量
' 此文件包含PowerPoint VBA编程中常用的常量定义
' 在VBA宏代码中引用这些常量可以方便地访问PowerPoint对象模型的各种功能

