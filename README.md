# MediMate — 智能用药安全助手 Agent

> **让每个家庭都有一位"随身药师"，通过 AI Agent 技术降低用药风险，守护家庭健康。**

| 字段 | 信息 |
|------|------|
| **产品名称** | MediMate 智能用药安全助手 |
| **产品类型** | AI Agent（医疗健康方向） |
| **目标用户** | 普通患者 / 家庭用药管理者 |
| **核心价值** | 通过 Agent 对话式交互，帮助用户查询药物信息、检测药物相互作用、了解真实不良反应数据 |

## 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| **前端** | Vue 3 + Vite | 深色主题、玻璃拟态 UI、SSE 流式渲染 |
| **后端** | Python FastAPI | 异步架构、SSE 流式输出 |
| **LLM** | DeepSeek API | Function Calling 驱动的工具调用 |
| **数据库** | Supabase PostgreSQL | 用药清单持久化（药物知识库、交互数据为内存缓存） |
| **外部 API** | OpenFDA FAERS | 真实不良反应报告数据 |

## 核心功能

| 功能 | 说明 | Agent 工具 |
|------|------|-----------|
| 💊 药物信息查询 | 输入药名，获取用途、剂量、注意事项 | `search_drug` |
| ⚠️ 药物相互作用检查 | 输入多种药物，检测冲突风险 | `check_interaction` |
| 📊 不良反应数据查询 | 调用 FDA FAERS 真实数据，条形图可视化 | `query_side_effects` |
| 📋 个人用药清单 | 维护用药清单，新增药物自动交互检查 | `manage_medication_list` |
| 🚨 紧急症状识别 | 检测危险描述，强制引导就医 | System Prompt 安全规则 |

## 核心亮点：Function Calling

LLM 自主决定调用哪个工具、传什么参数，实现真正的 AI Agent：

```
用户: "阿司匹林和华法林能一起吃吗？"
  → LLM 决策: 调用 check_interaction(["阿司匹林", "华法林"])
  → 工具执行: RAG 语义检索药物交互数据
  → LLM 生成: 自然语言风险提示 + 建议
```

## 快速启动

```bash
# 1. 启动后端
cd backend
pip install -r requirements.txt
cp .env.example .env  # 填入 DEEPSEEK_API_KEY 和 SUPABASE_DB_URL
uvicorn main:app --reload --port 8000

# 2. 启动前端
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173`

## 文档导航

### 产品文档（PRD）

| 文档 | 内容 |
|------|------|
| [01-产品愿景与背景](docs/01-产品愿景与背景.md) | 问题背景、核心痛点、市场数据 |
| [02-市场分析](docs/02-市场分析.md) | TAM/SAM/SOM、行业趋势、机会分析 |
| [03-竞品分析](docs/03-竞品分析.md) | 5 款竞品矩阵对比、竞争定位、差异化策略 |
| [04-用户研究](docs/04-用户研究.md) | 3 个 Persona 画像、用户旅程地图、Kano 模型 |
| [05-产品定位与策略](docs/05-产品定位与策略.md) | 产品定位声明、核心设计原则 |
| [06-功能需求](docs/06-功能需求.md) | 5 大核心 Feature 详细规格、完整对话示例 |
| [07-Agent架构设计](docs/07-Agent架构设计.md) | Function Calling 设计、System Prompt、上下文管理 |
| [08-交互设计](docs/08-交互设计.md) | 首次引导、核心对话流程、追问机制 |
| [09-安全与合规](docs/09-安全与合规.md) | 安全守卫、四级免责体系、数据隐私 |
| [10-数据策略](docs/10-数据策略.md) | 数据来源、知识库覆盖范围 |
| [11-成功指标](docs/11-成功指标.md) | 产品指标、体验指标、演示效果指标 |
| [12-风险分析](docs/12-风险分析.md) | 风险矩阵、伦理考量 |
| [13-Roadmap](docs/13-Roadmap.md) | 三阶段路线图、商业化路径 |
| [14-附录](docs/14-附录.md) | 技术栈选型、简历写法、参考资源 |
| [面试话术](docs/面试话术.md) | 完整面试话术（30秒陈述 + 6问回答 + 演示流程 + 追问应对） |

### 技术文档

| 文档 | 内容 |
|------|------|
| [PLAN.md](PLAN.md) | 技术实现指南（面向 AI / 开发者） |
| [PRD-Interview](docs/PRD-Interview.md) | 产品概要（面试精简版，聚焦架构决策与安全设计） |
