# GetAInews_skills

这是一个用于追踪 AI 最新动态的 Codex Skill 仓库，当前包含一个可直接使用的技能：

- `track-ai-updates`

这个 skill 主要用于抓取和整理以下平台上的 AI 发展、模型发布、研究进展、产品更新与社区信号：

- X
- Hugging Face
- 官方博客
- GitHub

输出形式默认是中文 HTML 简报，适合做日报、周报、专题快报和自动归档。

## 仓库结构

`track-ai-updates/` 目录包含完整 skill 资源：

- `SKILL.md`
  Skill 主说明，定义触发语义、工作流程和输出规范。
- `agents/openai.yaml`
  Skill 的 UI 与默认提示配置。
- `assets/`
  HTML 模板和示例配置文件。
- `references/`
  平台来源、HTML 展示风格等参考资料。
- `scripts/generate_ai_brief.py`
  自动抓取并生成中文 HTML 简报的脚本。

## Skill 功能

`track-ai-updates` 支持：

- 抓取 RSS / Atom 来源
- 汇总 Hugging Face、官方博客、GitHub 等平台的最新动态
- 通过可订阅 feed 接入 X
- 按关键词和时间范围过滤内容
- 自动生成带样式的中文 HTML 简报
- 通过输出目录模式按日期自动归档文件

## 安装与使用

如果你希望 Codex 自动发现这个 skill，可以把 `track-ai-updates/` 复制到本机的 skills 目录，例如：

```powershell
C:\Users\Guo\.codex\skills\track-ai-updates
```

随后即可在 Codex 中通过 `$track-ai-updates` 调用。

## 脚本使用说明

脚本文件：

```powershell
track-ai-updates\scripts\generate_ai_brief.py
```

示例配置：

```powershell
track-ai-updates\assets\source-config.example.json
```

### 1. 自动按日期归档输出

推荐用法：

```powershell
python track-ai-updates\scripts\generate_ai_brief.py --config track-ai-updates\assets\source-config.example.json --output-dir D:\papers\news --days 7 --max-items 18
```

运行后会自动生成类似下面的文件：

```text
D:\papers\news\ai-brief-2026-03-31.html
```

### 2. 手动指定输出文件名

```powershell
python track-ai-updates\scripts\generate_ai_brief.py --config track-ai-updates\assets\source-config.example.json --output D:\papers\ai-brief.html --days 7 --max-items 18
```

### 3. 离线演示模式

如果只想测试 HTML 页面生成链路，可以运行：

```powershell
python track-ai-updates\scripts\generate_ai_brief.py --demo --output-dir D:\papers\news
```

## 配置文件说明

配置文件使用 JSON，核心字段包括：

- `title`
  页面标题
- `subtitle`
  页面副标题
- `period`
  展示用时间范围
- `keywords`
  用于过滤和提升排序的关键词列表
- `sources`
  抓取源列表

每个来源支持：

- `name`
  来源名
- `platform`
  平台名，例如 `X`、`Hugging Face`、`GitHub`
- `type`
  `rss` 或 `atom`
- `url`
  feed 地址
- `priority`
  优先级，越高越容易排到前面
- `keyword_strict`
  可选，若为 `true`，则必须命中关键词才保留

## 关于 X

脚本不直接登录或模拟抓取 X 页面，而是建议通过可订阅 feed 来接入 X 内容，例如：

- RSSHub
- 自己维护的 X 转 RSS 服务
- 其他稳定的公开 feed 中转

这样更适合自动化运行，也更容易控制稳定性。

## 自动化建议

这个 skill 很适合做每天固定时间的自动简报任务，例如每天早上 8 点自动生成一份 AI 简报，归档到：

```text
D:\papers\news
```

建议让自动化执行：

```powershell
python C:\Users\Guo\.codex\skills\track-ai-updates\scripts\generate_ai_brief.py --config C:\Users\Guo\.codex\skills\track-ai-updates\assets\source-config.example.json --output-dir D:\papers\news --days 7 --max-items 18
```

## 输出特点

生成的 HTML 简报默认采用中文科技编辑部风格：

- 强标题
- 高信息密度
- 时间线展示
- 平台分区
- 适合桌面和移动端阅读

适合用于：

- AI 日报
- AI 周报
- 模型发布追踪
- 开源项目观察
- 产品更新汇总

## 后续可扩展方向

后续还可以继续扩展：

- 输出 `.json + .html` 双文件
- 加入更多平台源
- 接入更稳定的 X feed
- 自动生成“值得继续跟踪”板块
- 接入定时任务或 Codex automation
