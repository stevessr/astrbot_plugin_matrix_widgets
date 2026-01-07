# AstrBot Matrix Widgets Plugin

Matrix 小组件管理插件，提供在房间内添加、删除和管理小组件的命令。

## 依赖

- `astrbot_plugin_matrix_adapter`

## 命令概览

所有命令以 `/widget` 作为命令组前缀：

- `list` 列出当前房间小组件
- `add <name> <url> [type]` 添加小组件
- `remove <widget_id>` 移除小组件
- `jitsi [room_name]` 添加 Jitsi 会议小组件
- `etherpad [pad_name]` 添加 Etherpad 协作文档小组件
- `youtube <video_id|url>` 添加 YouTube 小组件
- `custom <widget_id> <name> <url> [type]` 添加自定义小组件

## 使用示例

```text
/widget list
/widget add "我的网页" https://example.com
/widget remove astrbot_abcd1234
/widget jitsi mymeeting
/widget etherpad notes
/widget youtube dQw4w9WgXcQ
/widget custom mywidget "我的工具" "https://example.com?room=$matrix_room_id"
```

## 说明

- 命令仅在 Matrix 平台生效。
- `custom` 命令支持 URL 模板变量：`$matrix_room_id`、`$matrix_user_id`、`$matrix_display_name`。
