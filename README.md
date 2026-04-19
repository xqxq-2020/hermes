# 英语宝 × Hermes Agent 自进化教学演示系统

本项目演示一套面向英语学习场景的 AI 教学闭环：从真实学情数据出发，识别个人弱项和班级共性问题，匹配听力、单词、绘本资源，生成下一轮可执行练习包，并给出 `MEMORY.md` / `USER.md` 的长期画像写回建议。

当前工作区已经接入真实数据样例：

- `data/260410_评测记录.csv`：个人口语评测记录，主学习者共 976 条记录。
- `data/260416_湘少四年级上册.csv`：四年级上册教材词汇掌握快照。
- `data/260415_听力专项.csv`：听力题资源库。
- `data/260415_巧记单词.csv`：单词资源库。
- `data/260415_绘本.csv`：绘本资源库。
- `skills/student-self-evolution/`：学情自进化 skill。
- `demo.html`：真实数据联动的可视化演示页。
- `evolution_brief.md`：脚本生成的学情诊断和练习包结果。

## 快速开始

### 1. 查看演示页

直接用浏览器打开：

```text
D:\eyyb\hermes\demo.html
```

页面包含四个核心演示区：

- 架构总览：展示真实数据如何进入 Hermes Agent 闭环。
- 四层记忆：展示个人证据、班级模式、资源目录如何分层沉淀。
- 练习包：展示听力、单词、绘本组合推荐。
- 自进化演示：展示从 brief 到 `MEMORY.md` / `USER.md` 写回建议的流程。

### 2. 安装一致的 uv 环境

项目使用 `uv` 管理 Python 运行环境，`uv.lock` 锁定依赖解析结果，`.python-version` 固定 Python 版本。团队成员和生产环境都应使用 frozen sync：

```powershell
uv python install 3.13.13
uv sync --frozen
```

如果 `uv` 默认缓存目录无权限，可指定工作区缓存。该目录已被 `.gitignore` 排除，不会上传：

```powershell
$env:UV_CACHE_DIR='D:\eyyb\hermes\.uv-cache'
uv sync --frozen
```

### 3. 重新生成学情诊断 brief

```powershell
uv run python skills/student-self-evolution/scripts/build_evolution_brief.py --workspace . --output evolution_brief.md
```

### 4. 验证脚本语法和 lock 文件

```powershell
uv run python -m py_compile skills/student-self-evolution/scripts/build_evolution_brief.py
uv lock --check
```

## 系统使用说明

### 面向演示人员

打开 `demo.html` 后，可以按以下讲解顺序演示：

1. 在“架构总览”中说明系统不是静态课件，而是读取真实评测、教材词汇和资源库。
2. 在“四层记忆”中说明哪些内容可以写入长期策略，哪些只是短期观察或资源信号。
3. 在“练习包”中点击手机演示按钮，展示听力识别、单词回忆、绘本迁移的生成过程。
4. 在“自进化演示”中推演下一轮练习，展示系统如何根据结果提出写回建议。

### 面向教研或运营人员

日常使用流程：

1. 将新导出的评测记录或资源目录放入 `data/`。
2. 运行 `build_evolution_brief.py` 生成 `evolution_brief.md`。
3. 审核其中的证据、推断、练习包和写回建议。
4. 只把稳定、重复、跨天或会改变教学策略的结论写入 `MEMORY.md` 或 `USER.md`。
5. 根据 Recommended Practice Pack 配置下一轮课中练习。

### 面向开发人员

主要入口：

- 演示页面：`demo.html`
- 学情分析脚本：`skills/student-self-evolution/scripts/build_evolution_brief.py`
- skill 说明：`skills/student-self-evolution/SKILL.md`
- 输出契约：`skills/student-self-evolution/references/output-contract.md`
- 演化规则：`skills/student-self-evolution/references/evolution-rules.md`

`demo.html` 当前采用页面内嵌 `realData` 的方式呈现演示数据。后续如需接入实时接口，可把 `realData` 替换为 API 返回结果，再复用页面已有的渲染函数。

## 功能介绍

### 1. 多源数据识别

脚本会自动识别当前工作区内支持的 CSV 类型：

- 个人口语评测：识别学习者、日期、内容、单词分、音素分、总体分。
- 教材词汇快照：识别班级词汇掌握、听力分、使用分、发音分、语义分、书写分。
- 听力资源目录：识别年级、单元、题量、题干集合。
- 单词资源目录：识别单词、释义、例句、音频、单元。
- 绘本资源目录：识别标题、年级、主题、词汇量、阅读时长、覆盖词。

### 2. 学情诊断

系统会把信号分成四类：

- direct evidence：直接证据，例如分数、日期、具体错词。
- inference：基于重复证据形成的谨慎推断。
- cohort pattern：班级或群体层面的共性模式。
- resource signal：资源目录信号，只用于选练习，不代表学生真实表现。

当前样例中的关键诊断：

- 主学习者有 976 条口语记录，时间覆盖 2026-04-07 至 2026-04-09。
- 总体均分 71.9，三天趋势为 75.23 → 72.63 → 63.88。
- 弱音集中在 `dh / s / uh / z / ng`。
- 弱词集中在 `between / This / students / total / twenty-seven`。
- 班级弱迁移词包括 `flower / these / garden / strong / a lot of`。

### 3. 推荐练习包

系统会根据薄弱词和年级，从资源库中生成组合练习包：

- 听力识别：先让学生在输入侧识别目标词或相关语境。
- 单词回忆：再做可控词汇复现。
- 绘本迁移：最后把词汇迁移到短句和语境中。

当前样例推荐：

- 听力：`Unit 1 The School Garden`、`Unit 4 These are flowers`
- 单词：`a lot of`、`always`、`between`、`colour`、`flower`、`garden`、`strong`、`these`
- 绘本：`Our Garden`、`Bees and Flowers`、`The ladybird who's lost without her friend`

### 4. 长期记忆写回建议

系统不会自动把所有观察写入长期文件，而是先给出建议：

- `MEMORY.md`：写教学策略、稳定模式、班级层面的教学动作。
- `USER.md`：写个人画像、个人弱项、互动节奏和纠正约束。

写回原则：

- 重复出现。
- 跨天或跨任务出现。
- 会改变下一轮教学动作。
- 能修正旧画像中的过时判断。

单次低分、资源目录信息、未验证推断不直接写入长期记忆。

## 核心架构

系统可以理解为四层闭环。

### 1. 数据层

数据层负责接收真实业务数据：

```text
data/
  260410_评测记录.csv
  260416_湘少四年级上册.csv
  260415_听力专项.csv
  260415_巧记单词.csv
  260415_绘本.csv
```

这些文件分别对应学生表现、班级词汇状态和教学资源目录。

### 2. 诊断层

诊断层由 `build_evolution_brief.py` 实现，主要负责：

- 自动检测 CSV schema。
- 分离个人证据、班级模式和资源信号。
- 统计弱音、弱词、趋势和资源覆盖。
- 生成 micro-loop 和练习包。
- 输出 `evolution_brief.md`。

### 3. 记忆层

记忆层由 `MEMORY.md` 和 `USER.md` 表达：

- `MEMORY.md` 保存稳定教学策略。
- `USER.md` 保存个人学习画像。

这两个文件不是日志，不记录所有原始事实，只保留可复用、可指导下一轮教学的结论。

### 4. 展示层

展示层由 `demo.html` 实现：

- 读取当前已整理出的真实指标。
- 可视化数据流、记忆分层、练习包和写回流程。
- 用交互动画说明系统如何从数据走到教学动作。

当前是静态页面，适合产品演示、方案讲解和内部评审。

## 核心思想

### 证据优先

系统先看真实评测和业务数据，再生成教学动作。资源库本身不代表学生能力，只能支持选材。

### 分层记忆

短期观察、长期策略、个人画像和资源目录分开处理，避免把一次性现象写成固定标签。

### 小步闭环

每次只抓一个主目标、一到两个纠正点、一条从易到难的练习路径。当前默认推荐：

```text
听力识别 -> 单词回忆 -> 绘本迁移
```

### 稳定再写回

只有当证据足够稳定，才建议更新 `MEMORY.md` 或 `USER.md`。这能防止系统因为单次异常表现过度调整教学策略。

### Skill 化复用

当一个分析和教学流程稳定后，沉淀为 skill。当前的 `student-self-evolution` skill 已经包含：

- 读数据。
- 分证据。
- 产 brief。
- 产练习包。
- 产写回建议。

## 扩展能力

### 1. 扩展新的数据源

可以在 `build_evolution_brief.py` 中新增 schema 判断和分析函数。例如：

- 作业批改记录。
- 课堂互动日志。
- 家长反馈。
- 语音声学特征。
- 单元测验成绩。

建议保持同样的证据边界：直接证据、推断、班级模式、资源信号分开。

### 2. 扩展新的练习资源

可以接入更多资源类型：

- 跟读句库。
- 自然拼读卡片。
- 互动游戏。
- 视频片段。
- AI 生成短故事。

新增资源时，应先定义资源字段，再设计匹配逻辑。不要把资源是否存在当成学生是否掌握的证据。

### 3. 扩展新的 skill

可参考当前目录结构：

```text
skills/
  student-self-evolution/
    SKILL.md
    scripts/
      build_evolution_brief.py
    references/
      evolution-rules.md
      output-contract.md
      prompt-recipes.md
    agents/
      openai.yaml
```

建议每个 skill 至少包含：

- `SKILL.md`：说明触发场景和工作流。
- `scripts/`：可重复执行的自动化脚本。
- `references/`：规则、输出契约、提示词模板。

### 4. 扩展展示层

当前 `demo.html` 使用内嵌 `realData`。后续可以升级为：

- 从 `evolution_brief.md` 自动解析数据。
- 从后端 API 拉取最新 brief。
- 增加学生选择器。
- 增加班级对比视图。
- 增加练习包导出按钮。

### 5. 扩展到 Hermes Agent 正式运行

当前工作区包含 `hermes-agent/`，可以把 `student-self-evolution` skill 接入 Hermes Agent 的技能体系，让智能体在真实对话中调用同一套分析流程。

接入重点：

- 保持 `MEMORY.md` / `USER.md` 的写回边界。
- 保持资源目录只用于选材。
- 对自动写回增加人工审核或阈值控制。

## 部署方式

### 依赖和版本锁定

本项目用 `uv` 管理 Python 环境：

- `pyproject.toml`：声明项目元信息和 Python 版本约束。
- `.python-version`：固定团队默认 Python 版本为 `3.13.13`。
- `uv.lock`：锁定依赖解析结果，保证团队和生产环境安装一致。
- `.uv-python/`、`.uv-cache/`、`.venv/`：本地环境和缓存目录，不提交到 Git。

标准安装流程：

```powershell
git clone --recurse-submodules https://github.com/xqxq-2020/hermes.git
cd hermes
uv python install 3.13.13
uv sync --frozen
uv lock --check
```

生产环境部署时也应使用 `uv sync --frozen`。不要在生产环境直接运行 `uv lock`，否则会重新解析依赖，破坏与仓库 `uv.lock` 的一致性。

### 方式一：本地静态演示

适用于方案讲解和产品演示。

步骤：

1. 保持 `demo.html`、`logo.jpg`、`evolution_brief.md` 在同一工作区。
2. 双击或浏览器打开 `demo.html`。
3. 如需更新数据，先运行 brief 生成脚本，再同步更新页面中的 `realData` 或接入解析逻辑。

优点：

- 无需服务端。
- 无需构建。
- 适合快速演示。

限制：

- 当前页面数据为静态内嵌。
- 不会自动读取本地 CSV。

### 方式二：本地脚本分析

适用于教研、运营或开发调试。

步骤：

1. 把新数据放入 `data/`。
2. 运行：

```powershell
uv run python skills/student-self-evolution/scripts/build_evolution_brief.py --workspace . --output evolution_brief.md
```

3. 打开 `evolution_brief.md` 审核结果。
4. 根据审核结果调整 `MEMORY.md` / `USER.md` 或下一轮练习包。

### 方式三：接入 Web 服务

适用于团队内部工具或在线演示。

建议架构：

```text
前端 demo 页面
  -> 请求 /api/evolution-brief
后端服务
  -> 调用 build_evolution_brief.py
  -> 读取 data/
  -> 返回 JSON 或 Markdown
前端
  -> 渲染指标、诊断、练习包、写回建议
```

实现建议：

- 后端可以用 FastAPI、Flask 或 Node.js 包装脚本。
- 脚本输出建议增加 JSON 模式，便于前端渲染。
- 写回 `MEMORY.md` / `USER.md` 前保留审核步骤。

### 方式四：接入 Hermes Agent

适用于真实智能体教学流程。

建议流程：

1. 将 `skills/student-self-evolution` 安装或挂载到 Hermes Agent 的 skill 搜索路径。
2. 在对话中触发学情更新或下一轮教学规划。
3. 由 Agent 读取 `MEMORY.md`、`USER.md` 和 `data/`。
4. 生成 brief、练习包和写回建议。
5. 经审核后写回长期记忆。

## 目录说明

```text
D:\eyyb\hermes
  demo.html                         # 可视化演示页面
  logo.jpg                          # 页面 logo
  README.md                         # 当前说明文档
  pyproject.toml                    # uv 项目配置
  uv.lock                           # 锁定依赖解析结果
  .python-version                   # 固定 Python 版本
  MEMORY.md                         # 长期教学策略记忆
  USER.md                           # 学生画像记忆
  evolution_brief.md                # 学情诊断与练习包输出
  data/                             # 原始业务数据
  skills/student-self-evolution/    # 学情自进化 skill
  hermes-agent/                     # Hermes Agent 主工程
  ppt/                              # 演示素材
```

## 注意事项

- 不要把资源目录中的字段直接写成学生表现。
- 不要因为单次低分重写学生画像。
- 不要把班级模式写入 `USER.md` 当成个人结论。
- 建议先生成 `evolution_brief.md`，人工审核后再写回长期文件。
- 如果新增数据 schema，先补脚本解析和输出契约，再更新演示页。

## 当前状态

- 已完成真实数据 brief 生成。
- 已完成 Recommended Practice Pack 输出。
- 已完成 `demo.html` 与真实数据联动。
- 已完成页面 logo 替换为 `logo.jpg`。
- 当前可作为本地静态演示和后续服务化改造的基础版本。
