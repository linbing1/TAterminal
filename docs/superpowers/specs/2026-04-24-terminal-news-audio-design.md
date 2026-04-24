# TAterminal 单篇新闻与音频工作流设计

**日期：** 2026-04-24
**状态：** 已完成设计，待用户 review
**适用环境：** macOS + iTerm2

## 背景

当前新闻抓取、分析、音频脚本与音频生成能力已经存在于相邻仓库 `../TAnews`。本次工作的目标不是重做内容流水线，而是在 terminal 中补一层足够轻的交互，让用户在 iTerm2 的任意 pane 里用两个短命令完成以下动作：

1. 拉取一篇值得看的英超文章
2. 在当前 pane 中快速浏览摘要
3. 对刚刚这篇文章生成音频并立即播放

用户的主要工作方式是：在多个 iTerm2 split pane 中并行工作，其中一个 pane 可能长期运行编译或 agent 任务，另一个 pane 用来快速消费新闻。第一版必须贴合这种工作流，不引入重交互界面。

## Goals

1. 提供两个命令：`ta news` 和 `ta audio`
2. `ta news` 每次只拉一篇文章
3. 选文规则固定为“评论数最高且未读”
4. `ta news` 在当前 pane 直接展示结果，并在展示成功后把文章标记为已读
5. `ta audio` 只处理刚刚由 `ta news` 选中的当前文章
6. 音频在本地生成并立即播放，命令返回后播放继续

## Non-Goals

1. 不做批量新闻摘要
2. 不做交互式 TUI
3. 不做自动新开 pane 或自动切 pane
4. 不做微信推送、GitHub Release 上传或远程托管
5. 不做播放控制台、暂停/继续、上一条/下一条
6. 不做跨平台支持，第一版只服务 macOS + iTerm2

## 命令模型

### `ta news`

职责：

- 从 The Athletic 英超流中找到“评论数最高且未读”的一篇文章
- 抓取全文并生成中文分析
- 在当前 pane 中打印适合 terminal 阅读的短输出
- 成功展示后，将该文章写入本地状态

成功后的状态变更：

- 将文章链接写入“已读集合”
- 将完整文章对象写入“当前文章”

### `ta audio`

职责：

- 读取“当前文章”
- 基于该文章生成口播稿
- 合成本地音频并立即播放

限制：

- 不重新选文
- 不自己拉新闻
- 若不存在当前文章，则直接失败并提示先执行 `ta news`

## 文章选择规则

`ta news` 的选文规则固定如下：

1. 拉取英超候选文章列表
2. 按评论数从高到低排序
3. 过滤掉已读文章
4. 取剩余文章中的第一篇

“是否已读”以文章链接作为主键判断。第一版不区分“已拉取”和“已听过”；只要 `ta news` 成功展示了该文章，就视为已读，后续默认不再重复返回。

## Terminal 展示

### `ta news` 输出结构

`ta news` 的输出必须适合在终端里快速扫读，因此只展示短结构，而不是整篇 Markdown：

1. 结果头
   例如：`[TA] next unread hot article`
2. 元信息
   包含标题、comment count、发布时间、原文链接
3. `Summary`
   3 到 5 句中文概述
4. `Why it matters`
   1 段更短的价值判断
5. `Next`
   明确提示可继续执行 `ta audio`
6. 状态尾行
   标明该文章已被记为 read，并已保存为 current article

### `ta audio` 输出结构

`ta audio` 不重复打印文章内容，只打印进度和结果：

1. `loading current article`
2. `generating audio script`
3. `playing audio`
4. 成功结果行：显示本地音频路径、时长、播放已启动

播放器启动后命令即可返回，避免阻塞当前 pane 的后续工作。

## 本地状态设计

本地状态不写入仓库目录，避免污染 git，也避免分支切换影响使用。统一使用用户目录下的状态根目录：

`~/.ta-terminal/`

第一版包含以下文件与目录：

- `~/.ta-terminal/current_article.json`
  - 保存最近一次 `ta news` 成功展示的当前文章
- `~/.ta-terminal/read_articles.json`
  - 保存已读文章链接集合
- `~/.ta-terminal/audio/`
  - 保存本地生成的音频文件

### `current_article.json`

建议至少包含：

- `link`
- `title`
- `comment_count`
- `published_at`
- `summary`
- `why_it_matters`
- `analysis_payload`

其中 `analysis_payload` 保留后续 `ta audio` 生成口播稿所需的最小信息，不要求原样复刻 `TAnews` 的全部调试输出。

### `read_articles.json`

第一版建议使用简单 JSON 数组，元素为文章链接字符串。原因：

- 数据量很小
- 可读、可手动排查
- 无需引入 sqlite 或其他状态层

## 模块划分

建议在 `TAterminal` 中拆分为 5 个薄模块：

1. `cli`
   - 解析 `ta news` / `ta audio`
   - 调用后续模块
2. `state_store`
   - 读写 `current_article.json`、`read_articles.json`、`audio/`
3. `tanews_adapter`
   - 复用 `../TAnews` 的文章收集、全文抓取、分析、口播稿能力
4. `renderer`
   - 把分析结果渲染为适合 terminal 的短输出
5. `audio_player`
   - 负责音频合成和 macOS 本地播放

关键原则是边界清楚：

- `TAnews` 提供内容能力
- `TAterminal` 提供单篇命令工作流、状态管理和终端交互

## 数据流

### `ta news`

1. CLI 进入 `news` 子命令
2. `tanews_adapter` 拉取候选文章
3. `state_store` 用已读链接集合过滤候选
4. 选出评论数最高的未读文章
5. `tanews_adapter` 抓全文并生成中文分析
6. `renderer` 在当前 pane 打印精简结果
7. `state_store` 在展示成功后更新：
   - `current_article.json`
   - `read_articles.json`

### `ta audio`

1. CLI 进入 `audio` 子命令
2. `state_store` 读取 `current_article.json`
3. `tanews_adapter` 基于当前文章生成口播稿
4. `audio_player` 合成本地音频文件
5. `audio_player` 调用 macOS 播放器后台播放
6. CLI 输出结果并返回

## 与 `TAnews` 的集成方式

第一版不建议直接复用 `TAnews` 的整条 pipeline。原因如下：

- `TAnews` 的主入口面向“整批摘要 + 推送”
- 当前需求面向“单篇、terminal 内、当前 pane、串联命令”
- 若强行包现有 pipeline，命令语义会持续扭曲，后续扩展也会受限

因此推荐的集成方式是：

- 在 `TAterminal` 中写一个轻量适配层
- 直接复用 `TAnews` 内已经稳定的采集、全文抓取、分析、音频脚本能力
- 不复用其通知、批处理和远程托管路径

## 错误处理

### `ta news`

- 没有未读文章：
  - 输出 `no unread hot article found`
  - 不更新当前文章
- 抓取失败：
  - 输出失败原因
  - 不标记已读
- 分析失败：
  - 输出失败原因
  - 不标记已读
- 只有在终端成功展示之后：
  - 才写入已读记录
  - 才更新当前文章

### `ta audio`

- 没有当前文章：
  - 直接失败
  - 提示先运行 `ta news`
- 生成口播稿失败：
  - 直接退出
  - 保留当前文章不变
- 音频合成失败：
  - 直接退出
  - 保留当前文章不变
- 播放失败：
  - 输出错误
  - 保留本地音频路径，便于用户手动播放

## 测试重点

第一版优先验证以下行为：

1. `ta news` 会跳过已读文章，返回评论数最高的未读文章
2. `ta news` 只有在成功展示后才写入“已读”和“当前文章”
3. `ta audio` 只消费当前文章，不自行重新选文
4. 当当前文章缺失时，`ta audio` 会给出明确错误
5. 音频播放失败时，不会破坏当前文章状态

## 后续扩展方向

这些能力明确不在第一版范围内，但架构应当允许后续增加：

- `ta reset` 清空已读状态
- `ta replay` 重播最近一条音频
- `ta news --force` 临时忽略已读状态
- iTerm2 热键把 `ta news` / `ta audio` 绑定为更短操作
- 针对 terminal 输出增加颜色和更好的排版

## 实施建议

推荐按以下顺序进入实现：

1. 建 CLI 骨架与命令入口
2. 建本地状态层
3. 接入 `TAnews` 的候选文章拉取与单篇分析
4. 完成 `ta news` 的 terminal 渲染
5. 接入口播稿生成、本地合成与播放
6. 补齐错误路径和核心测试

## 备注

当前目录 `/Users/linbing/Project/github/TAterminal` 不是 git 仓库，因此本次只能写入设计文档，不能按标准流程执行 commit。若后续需要在该目录继续走 spec -> plan -> implementation 流程，建议先把该目录置于 git 管理下。
