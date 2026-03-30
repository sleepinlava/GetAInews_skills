---
name: track-ai-updates
description: 抓取并整理 X、Hugging Face、官方博客、GitHub 等渠道中的 AI 发展、模型发布、研究进展、产品更新与社区信号，并输出为中文 HTML 简报。适用于需要跟踪最新 AI 动态、汇总多平台进展、生成日报/周报/专题快报，或将零散信息整理成可视化网页摘要的场景。
---

# Track AI Updates

用于追踪 AI 领域的最新进展，并将结果整理成中文 HTML 页面。优先保证信息新、来源准、结构清晰、视觉呈现有层次。

## 快速使用

若需要自动抓取并落地生成 HTML 文件，优先使用脚本：

```powershell
python scripts/generate_ai_brief.py --config assets/source-config.example.json --output-dir D:\papers\news --days 7 --max-items 18
```

脚本会自动生成类似 `ai-brief-2026-03-31.html` 的文件名。

若想手动指定输出文件名，也可以继续使用：

```powershell
python scripts/generate_ai_brief.py --config assets/source-config.example.json --output D:\papers\ai-brief.html --days 7 --max-items 18
```

若只想验证 HTML 生成链路，可先运行：

```powershell
python scripts/generate_ai_brief.py --demo --output-dir D:\papers\news
```

脚本特点：
- 使用 Python 标准库，无需额外安装依赖
- 支持 RSS 和 Atom
- 支持按天数和关键词过滤
- 支持直接指定输出目录并按日期自动命名
- 自动生成带样式的中文 HTML 简报
- 可把 X 作为 RSS 源接入，例如 RSSHub 或其他可用的 X feed

## 工作流程

1. 先确认监控范围。
   常见范围包括：
   - 大模型发布
   - AI 产品更新
   - 开源项目与 GitHub 热点
   - Hugging Face 新模型、新 Space、新论文
   - X 上的重要讨论、演示、爆款线程
   - 特定主题，如 agent、视频生成、推理模型、评测框架

2. 优先从一手或近一手来源收集信息。
   推荐顺序：
   - 官方博客、发布页、更新日志
   - Hugging Face 模型页、Space、数据集页、论文页
   - GitHub 仓库、Release、Trending
   - X 上的官方账号、创始人、研究员、核心开发者
   - 媒体报道仅用于补充背景，不作为唯一依据

3. 只要涉及“最新”“最近”“今天”“本周”等时效性表述，就必须使用实时浏览验证。
   输出中必须写明具体日期，并附平台链接。

4. 过滤噪音，保留高价值信号。
   优先保留以下内容：
   - 新模型、新能力、新 benchmark
   - API、产品、价格、开放范围的重要变化
   - 社区快速传播的高质量 demo 或项目
   - 开源生态中的高增长仓库与工具
   - 对行业方向有启发的研究或讨论

5. 生成中文 HTML 简报。
   每条内容至少包含：
   - 标题
   - 日期
   - 平台
   - 发生了什么
   - 为什么重要
   - 来源链接
   - 可选：可信度或“影响判断”为推断的说明

## 自动抓取脚本约定

### 配置文件

脚本读取 JSON 配置，核心字段如下：
- `title`：页面标题
- `subtitle`：页面副标题
- `period`：展示用时间范围
- `keywords`：关键词过滤列表
- `sources`：来源数组

每个来源支持：
- `name`：来源名
- `platform`：平台名，如 `X`、`Hugging Face`
- `type`：`rss` 或 `atom`
- `url`：feed 地址
- `priority`：优先级，数值越高越容易排到前面
- `keyword_strict`：可选，若为 true，则必须命中关键词才保留

### X 的处理方式

脚本不直接模拟登录抓取 X 页面，而是把 X 视作“可订阅 feed 源”。
推荐接入：
- RSSHub
- 你已有的 X 转 RSS 服务
- 其他稳定的公开 feed 中转

这样更稳定，也更容易自动化落地。

## 平台抓取要点

### X

X 适合发现最早期的发布信号、讨论热度、演示视频和社区反馈。

优先查看：
- 官方实验室账号
- 创始人和研究负责人账号
- 高频发布 demo 的开发者账号
- 被多个可信账号反复引用的话题链路

处理原则：
- 若 X 帖子附带博客、论文、模型卡、仓库链接，优先跳转到原始页面核实
- 不要只依赖转述帖判断事实
- 若结论来自社区讨论而非官方确认，需要明确标注

### Hugging Face

Hugging Face 适合观察模型、Space、数据集、论文和社区复用情况。

重点检查：
- 模型更新时间
- 任务标签与许可证
- Space 演示是否可用
- 是否链接 GitHub 仓库
- 是否反映出新的能力方向或应用范式

### 官方博客与产品渠道

用于确认正式发布、能力更新和路线变化。

重点关注：
- 发布博客
- changelog
- 文档更新
- 模型说明页
- 价格、权限、API 变更

### GitHub

用于确认开源项目热度和真实工程进展。

重点关注：
- 新 Release
- Star 增长快的仓库
- 最近提交是否活跃
- issue/discussion 是否表明社区快速采用

## HTML 输出规范

默认输出为单文件 HTML，适合直接预览或后续部署。除非用户明确要求，否则不要只输出 Markdown。

### 结构要求

HTML 页面建议包含以下区块：
- 顶部主视觉区：标题、副标题、日期范围、数据来源概览
- 重点摘要区：3-5 条最值得先看的结论
- 动态时间线区：按时间或重要性排列的更新
- 平台分栏区：X、Hugging Face、官方博客、GitHub
- 趋势观察区：总结阶段性变化与值得继续跟踪的话题
- 页脚：数据来源说明与生成时间

### 视觉要求

参考前端优化思路，页面应满足：
- 第一屏像“科技情报海报”，而不是普通表格
- 强调标题层级和留白，不堆砌卡片
- 默认使用 1 个主色和 1 个强调色，避免紫色泛滥
- 尽量使用分区、时间线、列表、分栏，而不是满屏小卡片
- 信息密度要高，但可扫读性必须强
- 移动端和桌面端都应可读

### 推荐设计方向

默认采用“科技编辑部简报”风格：
- 深色墨黑或浅色纸白二选一，但整页风格必须统一
- 标题强、正文克制、重点信息用标签或细边框强调
- 可以加入轻量渐变、网格纹理或时间线高亮
- 动效只做轻量进入或 hover 强调，不做花哨动画

### 编码要求

生成 HTML 时：
- 使用语义化标签，如 `header`、`main`、`section`、`article`、`footer`
- CSS 优先写在同文件 `style` 中，便于直接打开查看
- 若使用 JavaScript，只做筛选、折叠、轻量交互
- 所有外链必须明确可见
- 日期统一使用绝对日期，如 `2026-03-31`

## 输出模版建议

若用户未指定版式，优先使用以下信息组织方式：

1. 顶部一句话总结本期 AI 动态
2. 列出 3 条最重要变化
3. 用时间线列出主要更新
4. 按平台补充更多发现
5. 最后写“值得继续跟踪”

## 质量标准

- 宁可保留 5 条强信号，也不要堆 20 条弱信息
- 每条都要尽可能有原始链接
- 明确区分事实、评价、推断
- 同一事件若来自多个来源，优先保留最原始、最完整的一条
- 如果信息不充分，要明确说不确定，不要补写成确定结论

## 参考资料

需要候选来源、检索方向和 HTML 展示细则时，读取：
- [references/platforms.md](references/platforms.md)
- [references/html-brief.md](references/html-brief.md)
- [assets/ai-brief-template.html](assets/ai-brief-template.html)
- [assets/source-config.example.json](assets/source-config.example.json)
- [scripts/generate_ai_brief.py](scripts/generate_ai_brief.py)
