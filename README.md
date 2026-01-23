# AstrBot Matrix Widgets Plugin

Matrix 小组件管理插件，提供在房间内添加、删除和管理小组件的命令，以及多平台音乐点歌功能。

## 依赖

- `astrbot_plugin_matrix_adapter`
- `aiohttp`

## 命令概览

### 小组件管理 `/widget`

- `list` 列出当前房间小组件
- `add <name> <url> [type]` 添加小组件
- `remove <widget_id>` 移除小组件
- `jitsi [room_name]` 添加 Jitsi 会议小组件
- `etherpad [pad_name]` 添加 Etherpad 协作文档小组件
- `youtube <video_id|url>` 添加 YouTube 小组件
- `custom <widget_id> <name> <url> [type]` 添加自定义小组件

### 音乐点歌 `/music`

- `search <关键词> [平台]` 统一搜索 (平台：netease/qq/youtube)
- `netease <关键词>` 网易云音乐搜索
- `qq <关键词>` QQ 音乐搜索
- `youtube <关键词>` YouTube 音乐搜索
- `spotify <track_id|url>` Spotify 播放
- `play <序号>` 播放搜索结果中的歌曲
- `mode <widget|link>` 切换输出模式

## 使用示例

### 小组件管理

```text
/widget list
/widget add "我的网页" https://example.com
/widget remove astrbot_abcd1234
/widget jitsi mymeeting
/widget etherpad notes
/widget youtube dQw4w9WgXcQ
/widget custom mywidget "我的工具" "https://example.com?room=$matrix_room_id"
```

### 音乐点歌

```text
/music netease 周杰伦 稻香
/music qq 林俊杰 江南
/music youtube lofi hip hop
/music search Taylor Swift youtube
/music play 1
/music mode link
/music spotify https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC
```

## 说明

- 小组件命令仅在 Matrix 平台生效。
- 音乐点歌支持两种模式：
  - `widget` (默认): 添加嵌入式播放器小组件到房间
  - `link`: 直接发送播放链接到聊天
- 非 Matrix 平台使用点歌功能时会自动回退到链接模式。
- `custom` 命令支持 URL 模板变量：`$matrix_room_id`、`$matrix_user_id`、`$matrix_display_name`。
