# Read Pilot（太子伴读）

<img src="assets/logo.png" alt="Read Pilot logo" width="220">

Read Pilot（太子伴读）是一个 Codex skill 和本地工具集，用来把长篇技术文章转换成中文伴读材料。

[English README](README.md)

它会生成：

- 结构化文章 JSON：摘要、章节笔记、术语表、复习问题
- 本地 HTML 阅读库
- 可复用的 Chrome 侧栏扩展，在原文页面旁边显示伴读笔记
- 本地 notes API，根据当前 URL 匹配对应文章笔记

Codex skill 名称是 `read-pilot`。

## 仓库结构

```text
.
├── SKILL.md                         # Codex skill 说明
├── assets/                          # Logo 和 Chrome extension 图标
├── agents/openai.yaml               # skill UI 元信息
├── references/article_json_schema.md # 文章 JSON 字段说明
├── scripts/
│   ├── fetch_article.py             # 抓取 URL 元信息和章节草稿
│   ├── render_library.py            # 把文章 JSON 渲染成本地 HTML 阅读库
│   ├── render_chrome_extension.py   # 生成可复用 Chrome extension
│   └── serve_library.py             # 启动本地页面和 notes API
└── demo/articles/                   # 一个示例文章 JSON
```

本地生成的阅读库不应提交到 git。默认可以放在 `library/` 或 `.tmp/`，这两个目录都已被忽略。

## 安装依赖

需要 Python 3。脚本依赖 `requests` 和 `beautifulsoup4`。

```bash
python3 -m pip install -r requirements.txt
```

## 作为 Codex Skill 使用

把这个仓库 clone 或复制到 Codex skills 目录，目录名使用 `read-pilot`。

```bash
mkdir -p ~/.codex/skills
git clone <repo-url> ~/.codex/skills/read-pilot
```

示例提示词：

```text
新增文章解析: https://example.com/post 用本地的 skill
```

## 手动工作流

先抓取草稿：

```bash
python3 scripts/fetch_article.py https://example.com/post --out .tmp/example.draft.json
```

参考 `references/article_json_schema.md` 补全中文伴读字段，然后把最终文章 JSON 保存到：

```text
library/data/articles/<slug>.json
```

渲染阅读库和扩展：

```bash
python3 scripts/render_library.py --library library
python3 scripts/render_chrome_extension.py --out library/extension
```

启动本地服务：

```bash
python3 scripts/serve_library.py --library library --port 8765
```

打开：

```text
http://127.0.0.1:8765/
```

notes API：

```text
http://127.0.0.1:8765/api/notes?url=<encoded-source-url>
```

## Demo

仓库内置一个示例文章 JSON：

```text
demo/articles/my-ai-adoption-journey.json
```

渲染到临时本地阅读库：

```bash
python3 scripts/render_library.py --library .tmp/demo-library --article demo/articles/my-ai-adoption-journey.json
python3 scripts/render_chrome_extension.py --out .tmp/demo-library/extension
python3 scripts/serve_library.py --library .tmp/demo-library --port 8765
```

然后访问：

```text
http://127.0.0.1:8765/
```

## 内容边界

对于普通受版权保护的在线文章，只保存伴读笔记、摘要、术语解释和简短结构线索。除非用户提供原文、文本属于公版，或用户有权转换该内容，否则不要把完整原文复制进本地 JSON。
