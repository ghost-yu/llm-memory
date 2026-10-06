# Titans 最小验证记录

本目录验证数学更新规则和第三方仓库的最小行为，不是论文表格的实验复现。代码提交固定为 `ce7da9e9a7909e95c8249ceece7c88000bc2c0b9`。

## 关联记忆任务 demo

在已有机制检查之外，已完成 [可运行 demo 与说明](demo说明.md)：直接调用第三方 NeuralMemory，演示线性参考与两层深记忆的合成关联任务。两层版本启用动量/遗忘，训练 400 步后写入查询 100%，重置后 12.74%；更新一个 key 后该 key 与其他 key 都正确。保存 checkpoint 重新加载所得五项指标与原结果一致。结果只适用于固定编码的 8-key 合成任务。

## 环境

- Windows，Python 3.12.14。默认 Anaconda Python 3.7.6 不符合仓库 `>=3.9` 要求；另查 Python 3.10 环境也未安装 torch。
- 约 15.7 GiB 系统内存；G 盘检查时约 45.3 GiB 可用。
- WMI 检测到 NVIDIA GeForce RTX 4060 Laptop GPU，不用 WMI 的 AdapterRAM 推定准确显存。此次为 CPU 环境，未验证 CUDA。
- 隔离环境：`复现/.venv`，不改变用户已有 conda 环境。
- 已安装 PyTorch `2.14.1+cpu`，仓库包 `0.4.12`；完整依赖见 `requirements.txt`。`pip check` 返回 `No broken requirements found.`。
- 仓库自带 `data/enwik8.gz`，未找到 `.pt/.pth/.safetensors` 模型权重。
- 不需要 API key，不访问付费模型；不用 enwik8 做全训练。

## 验证内容

`scripts/verify_memory.py` 执行五项检查：

1. 用 Python AST 解析仓库 7 个 Python 文件，检查语法。
2. 对式 (12) 的纯量完整平方损失，以有限差分核对参数梯度；按式 (13)–(14) 得到快权重 1 → 1.7 → 2.45。
3. 核对仿射递推的结合律和顺序递推结果，解释 parallel scan 的代数依据。
4. 直接导入第三方 `NeuralMemory`，随机输入 `[2,16,8]`，检查 shape、有限值、外层反向梯度、快状态变化、注册参数不被 forward 原地修改、带状态与重置状态对照、改变后缀后前缀不变。
5. 直接导入第三方 MAC 类，以 `[2,13]` 随机 token 输入，检查 logits `[2,13,32]` 与标量交叉熵及反向传播。

CPU 小配置将 accelerator/FlexAttention 关闭，采用 1 层 MAC、1 条 residual stream；不代表论文使用的训练规模和设置。固定随机 seed 方便复查，但不是多 seed 统计评测。

## 命令与证据

从 `G:\大模型记忆` 运行：

```powershell
& '.\Titans： Learning to Memorize at Test Time\复现\.venv\Scripts\python.exe' '.\Titans： Learning to Memorize at Test Time\复现\scripts\verify_memory.py'
```

`&` 在 PowerShell 中调用引号括起来的程序路径；第一个路径是隔离环境解释器，第二个路径是验证脚本。脚本内部按自身位置找到锁定仓库，结果写到 `outputs/verification.json`。

安装使用隔离环境 Python 的 `-m pip`。PyTorch CPU wheel 从 `https://download.pytorch.org/whl/cpu` 下载；网络中的依赖传输约 20 KB/s，完整 wheel 保留到 `wheels`，避免重传，再用明确的官方 PyPI 索引安装其余依赖。没有修改机器级 pip 配置。

为了避免重新下载较大的 NumPy，复制了 Codex 捆绑 Python 中的 NumPy 2.3.5 包、`numpy.libs` 和 dist-info 到此隔离环境。这些文件是独立副本，没有改变捆绑运行时；来源记录在 `outputs/numpy_origin.json`。随后 pip 的解析识别该已安装版本。

```powershell
& '.\Titans： Learning to Memorize at Test Time\复现\.venv\Scripts\python.exe' -m pip install '.\Titans： Learning to Memorize at Test Time\复现\wheels\torch-2.14.1+cpu-cp312-cp312-win_amd64.whl' '.\Titans： Learning to Memorize at Test Time\代码\titans-pytorch' --index-url https://pypi.org/simple
```

本地 wheel 明确使用 CPU、CPython 3.12、Windows amd64。仓库路径使 pip 安装下载并锁定的代码，而不是按同名包下载可能不同的源码。精确安装结果保存为 `requirements.txt`，该文件用于记录环境而不是声称跨机器完全可复现。

实际最后安装还把 `wheels` 中已完成的单个版本依赖（排除旧 fsspec/networkx/setuptools）作为 pip 的本地文件参数传入。以上命令是基础形式；重新运行时可添加 `--find-links '.\Titans： Learning to Memorize at Test Time\复现\wheels'` 使用保留文件。

安装前运行记录：`outputs/before_install.json`。前三项成功，仓库两项因缺少 `torch` 导入失败，这不说明论文算法失败。安装后的结果另见 `outputs/verification.json`，最终状态应以该文件为准。

## 实际运行结果

最终脚本退出码 0，五项全部通过。环境记录为 Python 3.12.14、PyTorch 2.14.1+cpu，CUDA 可用性为 false（这是 CPU 包的结果，不表示机器没有 NVIDIA GPU）。

| 检查 | 观测结果 | 可以支持的结论 |
|---|---|---|
| 语法 | 7 个 Python 文件解析成功 | 下载源码可被本解释器解析 |
| 梯度 | 解析值 -16，有限差分 -16.00000000046 | 纯量推演的求导与系数正确 |
| scan 代数 | 顺序和复合均为 0.1224 | 给定仿射输入时结合律成立 |
| NeuralMemory | `[2,16,8]` 输出，14 组有效反向梯度 | 此小配置可前向和反向 |
| 状态 | 快权重与初值最大差 0.50315；注册参数变化 0 | forward 在快状态中写入，没有原地更新注册参数 |
| 状态传递对照 | 继续状态与重置状态读出最大差 2.44574 | 显式传 state 会影响后续结果 |
| 后缀干预 | 前 8 个位置最大变化 0 | 所测神经记忆配置的前缀不受这个后缀修改影响 |
| 小 MAC | 12587 参数，logits `[2,13,32]`，交叉熵 3.71342，反向成功 | 小随机模型与标签路线可运行 |

NeuralMemory 检查中的 0.62375 是随机浮点读出的平方均值，不是语言模型指标。MAC 交叉熵也来自随机初始化和随机 token，不用于解释论文效果。

执行过程中依赖发出 `torch.jit.script` 弃用提示，不影响上述结果；没有开启 CUDA/FlexAttention 或生成测试。原仓库 `git status --short` 为空，没有为运行小检查修改第三方源码。

## 实验复现状态

**复现状态：部分成功（最小机制和仓库运行验证成功，论文实验未复现）。** 所有小验证通过只说明这些输入和配置下的代码可以运行，支持本文解释的状态更新机制。没有预训练、生成质量评估、RULER/BABILong、DNA 或时间序列实验；不能报告“已复现 2M 上下文”或论文性能。

后续若做效果复现，应先拿到匹配配置的权重和评测入口，再执行禁用写入/重置状态的受控子集评测。当前仓库示例使用字节词表、enwik8、AdoptAtan2 与多项扩展，直接运行 `train_mac.py` 不能重现论文 FineWeb-Edu/AdamW 结果。


## 本轮 skill 补齐的契约与形状观察

新增[脚本](scripts/trace_contracts.py)、[实测JSON](outputs/contracts_trace.json)、[内容核查记录](../资料/skill内容核查.md)。在G:/大模型记忆执行：

~~~powershell
$env:PYTHONIOENCODING='utf-8'
& '.\Titans： Learning to Memorize at Test Time\复现\.venv\Scripts\python.exe' '.\Titans： Learning to Memorize at Test Time\复现\scripts\trace_contracts.py'
& 'D:\anaconda\python.exe' '.\Titans： Learning to Memorize at Test Time\复现\scripts\audit_skill_revision.py'
~~~

第一条用已存在的隔离Python/PyTorch运行锁定原模块；第二条复查新文件/源码签名/JSON结果与本地链接。没有重新训练400步demo，也没有修改作者源码。输出新增15项边界检查，以及完整签名、状态维度、MAC边界记录。

原模块已复现一处失败：C=2，先T=5后续接T=3，store能接余段但forward读取处出现4与6的batch维不匹配；已在JSON保存错误。另测4→4整块续接成功；全False mask仍发生衰减，不代表状态被冻结。检查通过包含准确观察失败，不是全面证明源码正确。

运行中出现torch.jit.script弃用提示，执行完成。观测脚本初稿TensorDict直接迭代/装饰器inspect定位有错，已分别修正.keys()/inspect.unwrap；与未修复的原模块续接错误分别记录。
