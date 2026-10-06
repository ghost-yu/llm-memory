# LongMemEval 小 demo

数据为原始 LongMemEval_S，500题278 MB已下载并哈希校验。固定取六种源码类别各前10道非ABS题，共60，分别按session和用户turn执行原BM25，保存120条检索记录。时间部分为3候选合成机制例，Provider返回3条预设响应，不是真实模型推断。

原仓库提交8a44eb1bb033842b12c67c594ac2094fc3028526；作者仓库未修改。AST加载原索引、BM25分支、评分、merge、时间函数与原重排代码块，跳过CUDA/OpenAI工厂。未运行完整官方主程序。

环境：Windows，D:/anaconda/python.exe，Python3.7.6、NumPy1.21.6、Matplotlib3.1.3。rank-bm25 0.2.2仅装入本目录vendor，校验PyPI SHA256后保存wheel，本脚本优先使用vendor。官方环境要求Python3.9/Linux CUDA，与本小demo环境分开。

在G:/大模型记忆运行：

~~~powershell
$env:PYTHONIOENCODING='utf-8'
D:\anaconda\python.exe '.\LongMemEval： Benchmarking Chat Assistants on Long-Term Interactive Memory\复现\scripts\demo_longmemeval.py'
D:\anaconda\python.exe '.\LongMemEval： Benchmarking Chat Assistants on Long-Term Interactive Memory\复现\scripts\plot_results.py'
D:\anaconda\python.exe '.\LongMemEval： Benchmarking Chat Assistants on Long-Term Interactive Memory\复现\scripts\audit_delivery.py'
~~~

第一条做原代码检索与机制检查，第二条绘制实际结果，第三条逐ID核对评分和文件。无需API key或GPU。

[解释](../解释.md)、[源码](../代码/LongMemEval-historical/src/retrieval/run_retrieval.py)、[数据来源](../资料/数据/来源.json)、[结果](outputs/results.json)、[图](outputs/retrieval.png)、[审计](outputs/delivery_check.json)。

结果：按原始会话gold标注的60题session all@10=85%，不是QA正确率。原程序指标session all@10=88.33%，9题空gold造成虚增；排除空gold51题all@10=86.27%。turn有gold51题all@10=60.78%，两个粒度未按token预算等量比较。原NDCG的第二名不折扣，已用真实代码探针核验。

13项检查通过，其中包括原实现的限制现象。时间正确区间提升、错误区间损害排序，是合成机制检查；不汇入真实数据检索平均。

下载记录：Anaconda requests在HuggingFace重定向出现证书链错误；采用Node fetch的系统证书路径成功下载，未禁用证书验证。PyPI默认镜像找不到版本，官方pip远端也遇到证书问题；Node从官方PyPI下载校验wheel后本地pip安装成功。prepare.py末尾打印emoji遇到GBK输出错误，PDF提取、图片渲染、clone和checkout已完成；设置PYTHONIOENCODING=utf-8可重跑。download_data.py已有文件时只重验；本机首次下载使用的Node流程见来源URL及SHA256。

状态：部分成功。未做论文完整M/Stella/事实生成/CoN阅读/LLM judge复现，未制作全文翻译。

## 本轮函数契约与受控阅读提示

在G:/大模型记忆执行：

~~~powershell
$env:PYTHONIOENCODING='utf-8'
& 'D:/anaconda/python.exe' './LongMemEval： Benchmarking Chat Assistants on Long-Term Interactive Memory/复现/scripts/trace_contracts.py'
& 'D:/anaconda/python.exe' './LongMemEval： Benchmarking Chat Assistants on Long-Term Interactive Memory/复现/scripts/audit_skill_revision.py'
& 'D:/anaconda/python.exe' './LongMemEval： Benchmarking Chat Assistants on Long-Term Interactive Memory/复现/scripts/audit_delivery.py'
~~~

&调用指定解释器，次路径指定脚本，UTF-8避免旧终端输出编码失败；无额外CLI参数。第一条仅隔离原函数/语句，不import会在顶层跑60题的旧demo，不改数据/原results；第二条核14签名/28观察、来源、文件链接；第三条重查60题120排名/原13条件/原数据哈希和全部均值。新的contracts_stdout记录原打印与故意失败，人工内容核查独立。

实测PASS: 28 boundary checks; 14 signatures。包括assistant-only索引/缺标签/空gold/重复ranking、空扩展删除key与None区别、缺end时间JSON/无效日期、turn子串误匹配、prompt恢复round并pop原toy标签、useronly TypeError、两种k0/0token预算、受控CoN notes与judge Yesterday误判。constructor/工厂仅记录签名，仍跳过CUDA初始化；真实provider/schema/模型没有运行。词数tokenizer替代真实编码器，不由此声称实际prompt在所有模型预算内。

- [完整契约和原代码解释](../解释.md)
- [28条件/14签名](outputs/contracts_trace.json)
- [原打印和故意失败](outputs/contracts_stdout.txt)
- [内容逐项核查](../资料/skill内容核查.md)
- [来源/文件一致性](outputs/skill_revision_check.json)

环境3.7.6/NumPy1.21.6/vendor rank-bm25 0.2.2，Windows11Pro CPU；可见内存15.69GiB，G盘37.28GiB本轮快照。S278MB已下载，M/真实Stella/事实生成/日期推断/CoN回答/QA judge API未运行，状态仍**部分成功**。本轮prepare_prompt为受控toy原函数运行，与完整阅读模型复现区分。