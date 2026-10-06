# MIRAS 小 demo 运行说明

本目录复现论文的部分记忆机制：线性关联记忆的平方误差/Huber 在线写入、零梯度遗忘、log/Softmax 状态约束。不是完整 Moneta、Yaad 或 Memora 语言模型。主说明见[解释.md](../解释.md)。

## 已验证环境

复用相邻 Titans 目录的隔离环境：Python 3.12.14、PyTorch 2.14.1+cpu，CPU 单线程，float64。未修改系统 Python。requirements.txt 是该共享环境的完整包记录，不代表本脚本逐一用到其中每个包。

主实验只需要 PyTorch；画图使用本机原有 Anaconda Python 3.7.6 + Matplotlib 3.1.3。画图是读取已落盘结果，与实验环境分开，不重算或修改指标。若重建环境，CPU wheel 来源与版本须与 requirements 和环境记录一起核对，不能假定普通安装命令自动选择 CPU 包。

## 运行

在工作区根目录 G:\大模型记忆 打开 PowerShell：

~~~powershell
$t = Get-ChildItem -Directory | Where-Object Name -like 'Titans*'
$m = Get-ChildItem -Directory | Where-Object Name -like '*All Connected*'
& ($t.FullName + '\复现\.venv\Scripts\python.exe') ($m.FullName + '\复现\scripts\demo_miras.py')
python ($m.FullName + '\复现\scripts\plot_demo.py')
~~~

第一步运行真实张量更新并把输出写入本目录 outputs/demo_results.json。第二步使用当前系统 python 的 Matplotlib 读取 JSON 生成 PNG/SVG。完成实验必须先运行第一步。路径通过目录匹配取得，避免论文标题中的英文单引号破坏命令引用。

输出不存在时绘图会明确报错；没有网络、API key、GPU 或训练数据下载需求。主脚本退出码 0 表示所有断言通过，不代表原论文大模型指标被复现。

## 数据与指标

100 个独立 episode，种子从 2026 到 2125。每次 500 条观测，地址为 8 个 one-hot key，真实值交替为 ±1。两个更新器共享每个 episode 的输入流；α=1、η=0.2、δ=0.5。clean 流只有 std=0.05 的高斯噪声；contaminated 流中 3% 的观测额外带 ±20 偏移。主指标为第 251—500 步对八地址的 mean absolute error，再跨 episode 平均。

这不是人为挑出一条最好的曲线；图中间明确只展示 seed=2026 的示例，聚合分数来自 100 个 episode。误差棒表示均值标准误。常态更新适应反例另从已记住的 1 开始，真实值永久改为 3。

## 实测结果

| 流 | L2 | Huber |
|---|---:|---:|
| clean 后半段平均误差 | 0.013288 | 0.013321 |
| 3% outliers 后半段平均误差 | 0.529372 | 0.022535 |
| 真实值 1→3，达到误差 <0.1 的更新次数 | 14 | 23 |

解析梯度与 autograd 核对通过；保留率 α=0.98 的零梯度更新通过；Memora 公式 27 的每列 normalization 不变量通过。归一化切片是本地教学选择，未找到官方完整 MLP 实现来核实。

## 文件与复现状态

- [原始结果](outputs/demo_results.json)：配置、环境、跨 episode 统计、示例轨迹、断言相关数值。
- [结果图](outputs/demo_summary.png)与[SVG](outputs/demo_summary.svg)：使用实测 JSON 绘制。
- [实验代码](scripts/demo_miras.py)：main → checks/生成数据 → write → 评估 → JSON。
- [绘图代码](scripts/plot_demo.py)：读取结果后绘图。
- [环境锁定记录](requirements.txt)：复用环境包清单。

状态为部分成功：内容精读与机制 demo 已完成；完整语言模型训练、chunk 并行、原论文表格指标未复现。主代码没有外循环训练，不生成或需要 checkpoint。固定阈值的 Huber 写入只限制大残差影响，不识别观测真假。

## 本轮函数契约与边界检查

在同一工作区根目录和同一 Titans 隔离环境运行：

~~~powershell
$t = Get-ChildItem -Directory | Where-Object Name -like 'Titans*'
$m = Get-ChildItem -Directory | Where-Object Name -like '*All Connected*'
& ($t.FullName + '\复现\.venv\Scripts\python.exe') ($m.FullName + '\复现\scripts\trace_contracts.py')
& ($t.FullName + '\复现\.venv\Scripts\python.exe') ($m.FullName + '\复现\scripts\audit_skill_revision.py')
~~~

Get-ChildItem/Where-Object 取得两个论文目录，& 调用指定解释器，不依赖全局 python。第一个脚本导入原 demo 并核对5个真实函数签名、数值更新、状态不变、错误输入、Huber多维差异和归一化范围；还重放seed2026污染episode、shift与checks，和存档逐项比较。它不重跑全部200个episode，不改主源码或原结果。第二个脚本检查这些运行证据与当前源文件和文档的哈希、链接、结构是否一致，**不能自动判定中文讲解语义正确**。

实测输出：trace退出码0，PASS: 13 contract/boundary checks。两种模式各重放500条误差，seed2026有13次污染，shift仍为14/23步。错误mode和key维度案例被拒绝；向量value的广播可接受，但不能据此支持多输出记忆。具体见[contracts_trace.json](outputs/contracts_trace.json)及[skill_revision_check.json](outputs/skill_revision_check.json)。内容与原文的逐条对照见[内容核查](../资料/skill内容核查.md)。

资源检查：当前机器是 Windows 11 专业版，总可见内存约15.69 GiB（Get-CimInstance Win32_OperatingSystem 返回16454352 KiB）；本次脚本 CPU 单线程、float64，不请求GPU或API，数据由本地生成。没有权重、许可证或联网训练数据依赖；这一运行成本不代表原论文15B—100B tokens训练成本。历史原实验已落盘；新增追踪只需秒级运行与少量输出文件空间。PDF文本输出曾因系统GBK终端不支持字符失败，设 PYTHONIOENCODING=utf-8 后提取成功，这是输出编码问题而非模型失败。

本轮资源快照：G盘空闲约37.34 GiB（Get-PSDrive G）；新增核验脚本首次运行遇到输出报告尚未生成的自身链接，已将该唯一目标延后至写入后验证，再次运行退出码0。该问题属于核验脚本初始化，不影响原demo结果。
