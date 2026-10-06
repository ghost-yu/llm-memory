# Nested Learning / CMS demo 运行说明

范围：论文 CMS 的链式 MLP 与周期梯度更新。本地教学实验，不是完整 Hope。主说明见[解释.md](../解释.md)。

## 环境与运行

复用相邻 Titans 的隔离环境：Python 3.12.14、PyTorch 2.14.1+cpu，float32、CPU 单线程。requirements.txt 是共享环境完整包清单，主脚本只直接依赖 PyTorch。不需要 GPU、API key、网络或数据下载。

在 G:\大模型记忆 的 PowerShell 执行：

~~~powershell
$t=Get-ChildItem -Directory | Where-Object Name -like 'Titans*'
$n=Get-ChildItem -Directory | Where-Object Name -like 'Nested*'
& ($t.FullName+'\复现\.venv\Scripts\python.exe') ($n.FullName+'\复现\scripts\demo_cms.py')
python ($n.FullName+'\复现\scripts\plot_demo.py')
~~~

第一步运行实验并保存 JSON/checkpoint。第二步用现有 Anaconda Python 3.7.6、Matplotlib 3.1.3 和 NumPy 读取 JSON 绘图，不重算或修改指标。若重建环境，CPU wheel 来源与锁定清单一起核对，不假定普通安装命令自动选择 CPU 版本。

## 配置与数据

每个模型为 3 个残差块：Linear(8,32)→GELU→Linear(32,8)，总计 1,656 参数。先用 A 监督训练 300 步，再复制同一状态给三个对照。这不是论文的多层元学习，也不使用 Llama 权重。

输入为 8 个 one-hot 地址，每批包含全部八个地址。A 是 identity 映射；B 保持前四个地址不变、后四个目标循环移位。A 128 步→B 256 步→再次 A 256 步，总 640 步。五种种子为 31—35。每步先读取评价，再用当前标签更新。

周期分别是 every_step=[1,1,1]、cms=[1,16,64]、all_slow=[64,64,64]。每块累积梯度，到期用 lr/C 乘求和梯度，等价于均值梯度；同一步所有梯度求完后才应用更新。学习率为 0.1。

## 实测结果与限制

| 指标 | Every step | CMS | All slow |
|---|---:|---:|---:|
| 每块更新次数 | 640/640/640 | 640/40/10 | 10/10/10 |
| B 首次读对改变地址，平均相对步数 | 86.0 | 100.0 | 未达到 |
| 再提供 A 后首次读对改变地址，平均相对步数 | 44.8 | 33.2 | 1.0 |
| B 末尾旧 A 的 MSE | 0.090620 | 0.123535 | 0.000350 |

All slow 的 A“恢复快”源于没有学会 B。CMS 在 B 阶段旧 A 的误差反而更大，本实验不证明总能减少遗忘。恢复需要重新收到 A 的标签，不是自动找回旧事实。

块更新总次数从 1,920 到 690；三个模型仍每步进行 forward 与全部参数求梯度，不能把次数减少等同于耗时/FLOPs 减少。不同周期的有效更新总量也不同，不将差异全部归因于单一因素。

首次 accuracy 达标不等于低 MSE 或稳定收敛。这是已知地址回忆，不是 held-out 泛化。曲线为五 seed 的写入前均值；JSON 的边界 snapshot 是写入后指标，分开记录。

## 文件与检查

主实验退出码 0，周期计数、未到期块不改参数、有限读取检查通过；累积均值梯度与 batch 梯度检查误差为 0。checkpoint 重新加载后参数 Tensor 完全相同。交付核验进一步比较 seed=31 重载读取结果与最终快照。

- [实验代码](scripts/demo_cms.py)与[绘图代码](scripts/plot_demo.py)。
- [原始结果](outputs/demo_results.json)：每 seed 轨迹、实际 change_log、配置和指标。
- [PNG](outputs/demo_summary.png)与[SVG](outputs/demo_summary.svg)。
- [toy checkpoint](outputs/toy_cms_checkpoint.pt)：seed=31 的三种本地模型，不是原论文权重。
- [交付检查](outputs/delivery_check.json)：文件散列、链接及轨迹一致性核验。

复现状态：部分成功。本篇内容和 CMS 小 demo 完成；完整 Hope、DGD、M3、外循环元学习、chunk 并行、原规模语言模型及 10M BABILong 未复现。

## 本轮函数契约与梯度路径检查

~~~powershell
$t=Get-ChildItem -Directory | Where-Object Name -like 'Titans*'
$n=Get-ChildItem -Directory | Where-Object Name -like 'Nested*'
& ($t.FullName+'\复现\.venv\Scripts\python.exe') ($n.FullName+'\复现\scripts\trace_contracts.py')
& ($t.FullName+'\复现\.venv\Scripts\python.exe') ($n.FullName+'\复现\scripts\audit_skill_revision.py')
& ($t.FullName+'\复现\.venv\Scripts\python.exe') '资料\check_nested.py'
~~~

Get-ChildItem/Where-Object找到论文目录，&调用指定解释器。第一步导入原demo，读取11个真实签名，以[1,2,4]做4步真实反传和周期更新，对照独立期望参数/缓冲；再测试慢块参数不变但输出变化、错误周期、短列表和3组checkpoint重载。第二步检查源文件散列、运行证据、链接和文档结构，不自动证明中文内容正确。第三步重新核查旧实验的5 seeds/3 modes/640 steps轨迹和快照。

第一步实测退出码0：PASS: 16 contract/boundary checks; 11 actual signatures。证据见[contracts_trace.json](outputs/contracts_trace.json)和[skill_revision_check.json](outputs/skill_revision_check.json)；内容逐项对照见[内容核查](../资料/skill内容核查.md)。原主实验源码和数字未修改，不为解释重新挑选种子或改指标。

重要边界：periods需与3块匹配且为正整数，主调度器未主动校验；过短列表可静默漏块，0周期在update报ZeroDivisionError且此前steps已增加。这些是保存的误用观察，检查通过不表示所有参数组合无bug。冻结某慢块不会冻结其上游输入；训练loss=4×全元素MSE（本配置D=8）。checkpoint含模型状态，不含任意半周期恢复所需的accum/steps/phase；当前640步恰逢周期边界仍需手工重建训练状态。

资源快照：Windows 11专业版，可见内存16454352 KiB（约15.69 GiB），G盘空闲37.32 GiB；CPU单线程float32。新增小检查含4步更新与原checkpoint读取，秒级完成；不下载数据、权重，不调用GPU/API，不需要新增许可证。该资源用量不代表原Hope的30B/100B tokens或10M context实验成本。读取PDF文本时使用PYTHONIOENCODING=utf-8，避免系统GBK编码造成字符输出失败。
