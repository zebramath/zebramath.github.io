# 主页维护指南

站点内容与展示层已经分离。日常更新通常只需要修改 `data/` 或 `content/`，无需碰 HTML/CSS。

## 最常用的更新

### 添加课程或资料

编辑 `data/academic.yaml`：

- 新课程：复制一个 `courses` 条目，修改 `code`、中英文标题、学期和资源组。
- 单个 PDF：添加到 `items`，填写中英文标题和 `/docs/...` 路径。
- 连续编号作业：使用 `batch`，只需填写目录规则和数量。

PDF 文件仍放在 `static/docs/`。页面会自动统计每门课程的资源数。

### 添加游戏

编辑 `data/hobbies.yaml` 中的 `games`。Steam 游戏只需填写：

```yaml
- title: { zh: 中文名, en: English name }
  steam_appid: 123456
```

页面会根据 `steam_appid` 自动生成 Steam 商店链接和封面。游戏清单只收录 Steam 游戏，页面统一显示为玩过的游戏，不需要维护平台、类型或游玩状态。

Steam 与豆瓣个人主页入口写在 `content/hobbies.md` 和 `content/hobbies.en.md` 的正文列表中。`excluded_steam_appids` 用来阻止工具类应用被自动同步，当前已排除 tModLoader。

通常只需填写 `steam_appid`，页面会使用标准 Steam 图片地址。如果某个新游戏使用了 Steam 新版的哈希图片路径，可像“原点计划”一样额外填写 `cover` 覆盖地址。

### 添加影视

少量添加时，直接编辑 `data/hobbies.yaml` 的 `media`。只要求 `title` 和 `type`，豆瓣链接、海报、年份与短评均为可选字段。

批量添加时，复制 `examples/media.csv`，删掉示例行后填入清单，再运行：

```bash
python scripts/import_media.py your-media.csv
```

结果会写入 `data/media_import.json`。这样不依赖非官方的豆瓣抓取接口，站点构建也不会因为第三方服务波动而失败。

也可以从公开的豆瓣“看过”页面同步全部影视。以当前账号为例：

```bash
python scripts/import_douban.py 275104236
python scripts/cache_douban_covers.py
```

第一条命令读取公开分页并写入 `data/media_import.json`，第二条把海报缓存到 `static/images/douban/`，避免豆瓣防盗链导致页面图片失效。两者都不需要密码或导出的登录 Cookie；豆瓣页面结构变化或触发访问验证时可能需要稍后重试。

自动导入不能可靠获得官方英文片名。需要修正英文名称时，只需在 `data/media_titles_en.json` 中用豆瓣条目 ID 添加覆盖项，例如：

```json
{
  "36600459": "The Shadow's Edge"
}
```

这份覆盖表与导入数据分离，再次同步豆瓣时不会丢失人工校正。

影视和游戏清单在同一个爱好页面内分页，默认每页显示 12 项。若需调整数量，只需修改 `data/hobbies.yaml` 中的 `settings.page_size`；电影、电视剧筛选、搜索与页码跳转会自动重新计算页数。

## Steam 自动同步（可选）

仓库包含 `Sync Steam library` 工作流。启用前：

1. 在仓库 Actions secrets 添加 `STEAM_API_KEY` 与 64 位 `STEAM_ID`。
2. 确保 Steam 游戏详情为公开可见。
3. 在 Actions 页面手动运行一次 `Sync Steam library`。
4. 如需每周自动更新，再创建 Actions variable：`STEAM_SYNC_ENABLED=true`。

脚本只把“游玩时间大于 0”的游戏写入 `data/steam.json`，不会把 API Key 写进仓库；已在 `data/hobbies.yaml` 精心维护的游戏会自动去重。

## 中英文内容

- 中文页面：`content/name.md`
- 英文页面：`content/name.en.md`

两个文件共享相同的 `name`，Hugo 会把它们识别为互译页面。导航栏的语言开关会自动出现。

## 本地预览

线上部署固定使用 Hugo Extended 0.164.0；本地也建议使用同一版本：

```bash
git submodule update --init --recursive
hugo server -D
```

提交前建议运行：

```bash
hugo --minify
```

推送到 `main` 后，现有 GitHub Pages 工作流会自动部署。
