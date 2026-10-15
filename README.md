# 大屏抛接静帧卡点视频

一个可复用的 Codex skill：**屏内人物抛出产品 → 第一视角快速接稳 → 旋转展示 → 静帧背景与成分逐字卡点**。

English: A reusable Codex skill and frame-accurate caption clock for screen-to-hand product reveal videos.

## 每次只换四项

| 输入 | 示例 |
|---|---|
| 背景 | 雨夜商业街、暖色电脑桌、电竞展馆 |
| 人物 | 指定英雄、真人coser、用户本人或模特 |
| 产品图 | 当前产品清晰包装图，保持品名、容量与标签一致 |
| 产品文案 | 用户提供，或由助手搜索同SKU的成分与检测资料 |

成片默认只出现成分、未检出条目、相应标题与编号，不自行增加“文案样稿”等说明字。

## 固定节奏

| 阶段 | 时间/帧 |
|---|---|
| 连续抛接 | 第0–96帧 |
| 短促旋转转场 | 第97–100帧 |
| 背景冻结、左侧第一项进入 | 第101帧，约3.37秒 |
| 右侧七页 | 第158、213、270、329、388、446、504帧 |
| 总长 | 563帧 / 30fps = 18.766667秒 |

画面为1280×720。背景冻结后仅产品轻微漂浮，文字继续展开；背景人物和车辆不循环。字长改变时，使用新字形宽度与原归一化展开曲线相乘，保留原出字时点。

## 安装

将本仓库克隆到 Codex 的个人技能目录（目录已存在时先自行选择其他位置，避免覆盖）：

**macOS / Linux**

```bash
git clone https://github.com/BarryD-777/screen-throw-freeze-video.git ~/.codex/skills/screen-throw-freeze-video
```

**Windows PowerShell**

```powershell
git clone https://github.com/BarryD-777/screen-throw-freeze-video.git "$env:USERPROFILE/.codex/skills/screen-throw-freeze-video"
```

若设置了自定义 `CODEX_HOME`，请改放到其 `skills` 子目录。在能发现该技能的新会话中调用：

> 用 $screen-throw-freeze-video 做一条。背景是雨夜街景，人物是站姿coser，产品用我上传的图，文案请搜索同款成分和检测依据。

## 工具与素材要求

- 卡点工具使用 **Python 3.9+**，只依赖标准库。
- 成片还需要当前环境的视频生成服务、图片工具及支持逐帧合成的渲染工具。可配合已安装的 Hypit 流程，或由其他工具按时钟实现；本仓库没有捆绑视频模型、API账户或完整渲染器。
- 用户自行提供可用的产品图、人物参考和有权使用的音乐。**原样片与BGM未随仓库发布**，本仓库也不授予第三方品牌、角色、音乐或照片的使用权。
- 固定时钟保留参考版的节奏，只有对应音乐从0秒原速播放时才能复现原来的音乐对齐。换曲需要重新检查，不能保证与任意歌曲自动卡点。

## 生成出字计划

先复制并填写 [`examples/copy.example.json`](examples/copy.example.json)。其中空列表用于说明结构，没有预设产品事实。

```bash
python scripts/make_cues.py --self-test
python scripts/make_cues.py --copy examples/copy.example.json --output outputs/cues.json
```

需要把音轨路径交给后续渲染器时：

```bash
python scripts/make_cues.py --copy your-copy.json --output outputs/cues-with-audio.json --audio local-media/your-licensed-track.m4a
```

不提供音乐也可生成时钟，输出的 `audio.requires_user_asset` 为 `true`。提供 `--audio` 时会检查文件是否存在。输出包含本地音乐的绝对路径，适合本机制作，不应提交到公开仓库；`outputs/` 默认忽略。

工具只生成 JSON，**不会直接输出视频**。它保留每行的起始帧、展开曲线、换页边界和全长；不补文案、不生成成分、不下载音乐、不调用收费API，且不会覆盖已有输出文件。

## 文案依据

“未列入成分表”“未添加”“不含”“检测未检出”有不同含义。请按当前SKU包装、官方资料或对应检测报告写文案，不从旧片或禁用成分表拼出150项。

左侧最多8项，右侧最多150项。资料不足时补资料或接受少项版本，保持空位隐藏；不要重复或编造条目来填满页面。来源记录在制作资料中，不添加到成片画面。

## 仓库内容

- [`SKILL.md`](SKILL.md)：技能入口和制作约束。
- [`assets/reveal-clock.json`](assets/reveal-clock.json)：逐帧归一化展开曲线。
- [`scripts/make_cues.py`](scripts/make_cues.py)：替换文案与音轨定位工具。
- [`references/accepted-timeline.md`](references/accepted-timeline.md)：完整时点、布局和数据格式。
- [`references/production-recipe.md`](references/production-recipe.md)：抛接连贯性、包装合成和静帧检查。
- [`references/copy-research.md`](references/copy-research.md)：成分与未检出文案的查证方法。

## License

本仓库中的代码、指令、文档和时钟数据采用 [MIT License](LICENSE)。用户自行提供的素材及所使用的外部服务适用各自的授权和条款。
