# Agent-Native CLI vs Model Context Protocol (MCP) 量化实证研究

本项目包含一套完整的基准测试框架，用于量化对比 **"Agent-Native CLI 工具"** 与 **"MCP (Model Context Protocol)"** 在当前大模型 Agent 操作系统（如 Claude Code, Cursor 等）中的最佳实践与性能鸿沟。

基于高德开放平台能力（Amap POI），我们构建了严格对等的双子星架构，并实测了它们在冷启动 Token 税、Unix 管道可组合性、错误隔离恢复及上下文维度上的核心差异。

## 🎯 核心结论速览
- **极客 CLI 的 Token 奇迹**：通过 `| jq` 将 JSON 过滤外包给底层 CPU，CLI 架构在复杂过滤中帮助 LLM 节省了高达 **80% 的单次推理 Token** 负担。
- **消灭协议税**：摒弃了全量加载所有工具 Schema 的做法，CLI 渐进式 `--help` 探索让平台规模再大也能保持恒定 **214 左右的极低首词预热 Token**（对比 MCP 20+ 工具时动辄上万 Token 的指数暴增）。
- **进程级极速容灾**：错误的输入直接触发系统级 `exit code` 并被沙箱安全回收，没有任何卡死与状态污染。

更为深度细致的实验推理细节，请参阅本仓库的硬核研报：
👉 **[experiment_results.md](./experiment_results.md) （强烈推荐阅读）**

---

## 🛠️ 仓库结构导览

| 文件/目录 | 作用说明 (Description) |
| :--- | :--- |
| `amap_cli.py` | 遵循极客语境设计的 **Amap-CLI 核心实体**。无花哨 UI，只吐纯净标准 JSON，极致迎合管道流 |
| `amap_mcp_server.py` | 基于真实环境模拟的 **MCP Server** 壳子，负责在 `tools/list` RPC 握手中压测海量 Schema 的负载 |
| `amap_api.py` | 纯净底层封装：实际桥接高德 RestAPI 的原生 SDK（含错误模拟探针） |
| `agent_runner_v2.py` | **核心 Benchmark 评测引擎**。包含严格并行的多个对照组实验（已挂载 Tiktoken 高精度统计与多次均值抹平逻辑） |
| `results_v2.json` | 引擎运转后沉淀的生肉基线压测数据池 |
| `experiment_results.md` | 基于 `results_v2.json` 降维提炼的深度架构趋势中文全解研报 |
| `walkthrough.md` | 记录开发历程与宏观反思的 Walkthrough 手记 |
| `requirements.txt` | Python 环境依赖清单 |

---

## 🚀 起步与运行 (Setup & Usage)

### 1. 环境准备
```bash
# 推荐使用虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装对应依赖包
pip install -r requirements.txt
```

### 2. 配置专属 API 密钥 (AK)
请在执行正式压测前，向系统环境变量中注入您的密钥（代码已进行绝对脱敏）：
```bash
# 高德开放平台 Web 服务的 Key
export AMAP_KEY="您的_高德_AK"

# 兼容 OpenAI 标准的大语言模型推断 Key (默认采用 ModelScope Endpoint)
export LLM_API_KEY="您的_大模型_AK"
```
*(如果不使用系统变量，也可以直接修改 `amap_api.py` 和 `agent_runner_v2.py` 头部的常量配置进行快速替换)*

### 3. 一键启动性能基准探针
```bash
python agent_runner_v2.py
```
终端将实时输出 N 轮重复采样的进度，并在结束后重新刷新覆盖同目录的 `results_v2.json` 。

---

## 💡 使用姿势体验 (CLI Demo)
即使撇去对比测试，您当下也可以立刻通过命令验证这段高内聚的 Unix 模块：
```bash
# 获取自我描述
python amap_cli.py search --help 

# 利用指令组合，直接将高德 JSON 输出用 jq 提纯出首个 POI 的纯净名称
python amap_cli.py search -k "星巴克" -c "北京" | jq -c ".data[0].name"
```

---

## 📜 许可与协议
此工程及相关调研论述仅供 AI 架构前沿社区和 AgentOS 爱好者研讨参考；高德相关底层 POI 数据权益及访问约束归属原服务商。
