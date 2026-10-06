# Zep 的 skill 内容核查

2026-10-05。本记录逐项对照 SKILL.md / reading-playbook；文件/哈希/签名脚本不能自动评判中文解释正确。依据本地2501.13956v1原PDF、正文抽取/渲染、77cb67cdfea7a080f217236b56f8ca39b25ca0e4原仓库、原demo与新增隔离执行。历史仓库未改动，非托管实验版本确认。暂不全文翻译、不要求原规模benchmark，遵从用户已选阅读边界。

| 要求 | 内容位置与直接证据 | 判断与边界 |
|---|---|---|
| 身份/边界 | 解释§1；原论文12页；资料/代码版本.json | v1及作者/日期、引擎与托管服务区别清楚 |
| 论文/仓库地图 | §1表；pyproject、graphiti.py、nodes/edges、maintenance/prompts/search、examples | 时间/图/检索/实验入口定位；完整LongMemEval入口未找到 |
| 可执行数据路径 | §3.1及7.1–7.2；原add_episode调用链和本地main→ingest | 不把隔离AST成功当原package导入/完整写库 |
| 目的—公式—类型—代码 | §2/4/5/7.4；G、T/T'、区间和f组合式 | 离散对象长度明确，1024仅论文embedding设置 |
| 公式协议 | §4/5.1/7.4；UTC/半开/乱序例子，RRF0索引分数 | 原符号与教学谓词区别，符号/步骤/例子/映射/等级齐全 |
| 图协议 | §6/7.4，原PDF确认无独立编号架构图；教学数据流 | 框/箭头/参数模型/无参数规则/类型/推理均写，未虚构原图 |
| 表协议 | §6.1–6.4；PDF表1–3、图片/page-7.png | 数据集/任务/score/延迟IQR、绝对相对差、公平性/成本限制；助手类别退步保留 |
| 核心函数契约 | §7.1；7原函数+13本地签名，另3原入口静态完整参数和main/ingest | 参数/默认/类型/返回/引用修改/调用链/论文/等级齐全 |
| 原代码协议 | §7.2三任务、7.3日期与fact修改、5.1 RRF | 目的/API/有效行/变量表/流/例子/等级，非只贴代码 |
| Python首次语法 | §3.1 async；7.2解包/star/条件式/dataclass/class/method；7.3推导式异常 | 本篇无PyTorch训练，不编造super/autograd；原BaseModel继承与替代校验区别清楚 |
| 连续形状流 | §3/5/7.2/7.3 | str→对象/列表→dict/日期→边→快照；召回embedding明确未运行 |
| 环境/命令/失败 | 复现README；原14checks/16响应；新增16checks/20签名 | Windows11Pro、3.12.14/标准库；naiveUTC假设、整数日期、相同起点、c=0实测；非自然语言抽取质量证明 |
| 文末六项 | §8 | 三等级/PaperCode含未找到/部分成功及证据/待解问题，整体九篇尚未完成 |

重点人工核对：
1. 原 get_edge_contradictions 在区间检查之前赋值旧fact；受控响应改变旧文本，即使resolve_edge_contradictions不重叠跳过，也不会恢复。真实模型/数据库回滚不在验证范围。
2. dedupe返回旧引用；resolve_extracted_edge的None回退保留原有效期，不清除已有终点。重复仍运行三个子任务。
3. ensure_utc对naive只加UTC，带+08:00则转换时刻；两者不能混为一谈。
4. 同起点矛盾因严格小于未解决；旧expired_at不会自动记录每次invalid_at修订。事务历史依赖教学快照，不是已跑原查询API。
5. 日期整数AttributeError属于绕过响应校验的隔离负例；坏字符串ValueError warning是原demo证据。
6. RRF rank_const0报错/单路重复加分/稳定同分，属于输入和实现性质，不证明检索质量。
7. Graphiti.search默认10仅返回edges，且改共享配方limit；未做并发测试。原add_episode返回AddEpisodeResults，不能照旧docstring写None。
8. 表2 4o相对增益由公布60.2→71.2算18.27%，论文18.5与四舍五入差异保留；延迟不等同全部历史写入成本。

资源快照：Windows11 Pro可见物理内存16454352KiB≈15.69GiB；G盘空闲37.28GiB（2026-10-05核查）。标准库隔离demo无需API/GPU/Neo4j，历史完整包、真实模型、数据/服务成本未经运行验证。原PDF/PNG及数据库既有证据保留。

运行证据：[新增追踪](../复现/outputs/contracts_trace.json)、[追踪脚本](../复现/scripts/trace_contracts.py)、[原demo](../复现/outputs/results.json)、[一致性核验](../复现/outputs/skill_revision_check.json)。新增16项全通过，其中负例是局限确认；原14项/16响应/5SQLite快照另由旧audit核验。审核范围是当前中文解读与小机制demo，不声称完整Zep、DMR/LongMemEval或线上收益已复现。

复现状态：**部分成功**。本篇修订核查完成；全项目还需A-MEM/LoCoMo/LongMemEval逐篇修订，不能据此结束九篇目标。