"""
Matrix Widgets Plugin - 提供 Matrix 小组件管理命令

此插件依赖于 astrbot_plugin_matrix_adapter 提供的 Matrix 客户端。
"""

import secrets
from typing import TYPE_CHECKING

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

if TYPE_CHECKING:
    from astrbot_plugin_matrix_adapter.client import MatrixHTTPClient


class Main(Star):
    def __init__(self, context: Context) -> None:
        super().__init__(context)
        self.context = context

    def _get_matrix_client(self, event: AstrMessageEvent):
        """获取 Matrix 客户端实例"""
        # 检查是否是 Matrix 平台
        if event.get_platform_name() != "matrix":
            return None

        # 尝试从平台适配器获取客户端
        try:
            for platform in self.context.platform_manager.platform_insts:
                meta = platform.meta()
                if meta.name == "matrix" and meta.id == event.get_platform_id():
                    if hasattr(platform, "client"):
                        return platform.client
        except Exception as e:
            logger.debug(f"获取 Matrix 客户端失败: {e}")

        return None

    @filter.command_group("widget")
    def widget_group(self):
        """Matrix 小组件管理命令"""

    @widget_group.command("list")
    async def widget_list(self, event: AstrMessageEvent):
        """列出当前房间的所有小组件

        用法: /widget list
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        room_id = event.get_session_id()

        try:
            widgets = await client.get_widgets(room_id)

            if not widgets:
                yield event.plain_result("当前房间没有小组件")
                return

            lines = ["**当前房间的小组件:**\n"]
            for w in widgets:
                content = w.get("content", {})
                widget_id = content.get("id") or w.get("state_key", "unknown")
                name = content.get("name", "未命名")
                widget_type = content.get("type", "unknown")
                url = content.get("url", "")
                creator = content.get("creatorUserId", "unknown")

                lines.append(f"- **{name}** (`{widget_id}`)")
                lines.append(f"  类型: {widget_type}")
                lines.append(f"  URL: {url[:50]}..." if len(url) > 50 else f"  URL: {url}")
                lines.append(f"  创建者: {creator}")
                lines.append("")

            yield event.plain_result("\n".join(lines))

        except Exception as e:
            logger.error(f"获取小组件列表失败: {e}")
            yield event.plain_result(f"获取小组件列表失败: {e}")

    @widget_group.command("add")
    async def widget_add(self, event: AstrMessageEvent, name: str, url: str, widget_type: str = "customwidget"):
        """添加小组件到当前房间

        用法: /widget add <名称> <URL> [类型]

        参数:
            name: 小组件显示名称
            url: 小组件 URL
            widget_type: 小组件类型 (默认: customwidget)

        示例:
            /widget add "我的网页" https://example.com
            /widget add "Jitsi会议" https://meet.jit.si/myroom jitsi
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        room_id = event.get_session_id()

        # 生成唯一的 widget ID
        widget_id = f"astrbot_{secrets.token_hex(8)}"

        try:
            result = await client.add_widget(
                room_id=room_id,
                widget_id=widget_id,
                widget_type=widget_type,
                url=url,
                name=name,
            )

            event_id = result.get("event_id", "unknown")
            yield event.plain_result(
                f"已添加小组件 **{name}**\n"
                f"ID: `{widget_id}`\n"
                f"类型: {widget_type}\n"
                f"URL: {url}"
            )

        except Exception as e:
            logger.error(f"添加小组件失败: {e}")
            yield event.plain_result(f"添加小组件失败: {e}")

    @widget_group.command("remove")
    async def widget_remove(self, event: AstrMessageEvent, widget_id: str):
        """从当前房间移除小组件

        用法: /widget remove <widget_id>

        参数:
            widget_id: 小组件 ID (可通过 /widget list 查看)

        示例:
            /widget remove astrbot_abc123
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        room_id = event.get_session_id()

        try:
            await client.remove_widget(room_id, widget_id)
            yield event.plain_result(f"已移除小组件 `{widget_id}`")

        except Exception as e:
            logger.error(f"移除小组件失败: {e}")
            yield event.plain_result(f"移除小组件失败: {e}")

    @widget_group.command("jitsi")
    async def widget_jitsi(self, event: AstrMessageEvent, room_name: str = ""):
        """快速添加 Jitsi 视频会议小组件

        用法: /widget jitsi [房间名]

        参数:
            room_name: Jitsi 房间名 (可选，默认自动生成)

        示例:
            /widget jitsi
            /widget jitsi mymeeting
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        room_id = event.get_session_id()

        # 生成房间名
        if not room_name:
            room_name = f"astrbot_{secrets.token_hex(6)}"

        widget_id = f"jitsi_{secrets.token_hex(8)}"
        jitsi_url = f"https://meet.jit.si/{room_name}"

        try:
            await client.add_widget(
                room_id=room_id,
                widget_id=widget_id,
                widget_type="jitsi",
                url=jitsi_url,
                name=f"Jitsi: {room_name}",
                data={
                    "domain": "meet.jit.si",
                    "conferenceId": room_name,
                },
            )

            yield event.plain_result(
                f"已添加 Jitsi 会议小组件\n"
                f"会议链接: {jitsi_url}\n"
                f"Widget ID: `{widget_id}`"
            )

        except Exception as e:
            logger.error(f"添加 Jitsi 小组件失败: {e}")
            yield event.plain_result(f"添加 Jitsi 小组件失败: {e}")

    @widget_group.command("etherpad")
    async def widget_etherpad(self, event: AstrMessageEvent, pad_name: str = ""):
        """快速添加 Etherpad 协作文档小组件

        用法: /widget etherpad [文档名]

        参数:
            pad_name: Etherpad 文档名 (可选，默认自动生成)

        示例:
            /widget etherpad
            /widget etherpad meeting-notes
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        room_id = event.get_session_id()

        # 生成文档名
        if not pad_name:
            pad_name = f"astrbot_{secrets.token_hex(6)}"

        widget_id = f"etherpad_{secrets.token_hex(8)}"
        # 使用公共 Etherpad 服务
        etherpad_url = f"https://etherpad.wikimedia.org/p/{pad_name}"

        try:
            await client.add_widget(
                room_id=room_id,
                widget_id=widget_id,
                widget_type="etherpad",
                url=etherpad_url,
                name=f"Etherpad: {pad_name}",
            )

            yield event.plain_result(
                f"已添加 Etherpad 协作文档小组件\n"
                f"文档链接: {etherpad_url}\n"
                f"Widget ID: `{widget_id}`"
            )

        except Exception as e:
            logger.error(f"添加 Etherpad 小组件失败: {e}")
            yield event.plain_result(f"添加 Etherpad 小组件失败: {e}")

    @widget_group.command("youtube")
    async def widget_youtube(self, event: AstrMessageEvent, video_id: str):
        """添加 YouTube 视频小组件

        用法: /widget youtube <视频ID或URL>

        参数:
            video_id: YouTube 视频 ID 或完整 URL

        示例:
            /widget youtube dQw4w9WgXcQ
            /widget youtube https://www.youtube.com/watch?v=dQw4w9WgXcQ
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        room_id = event.get_session_id()

        # 从 URL 提取视频 ID
        if "youtube.com" in video_id or "youtu.be" in video_id:
            if "v=" in video_id:
                video_id = video_id.split("v=")[1].split("&")[0]
            elif "youtu.be/" in video_id:
                video_id = video_id.split("youtu.be/")[1].split("?")[0]

        widget_id = f"youtube_{secrets.token_hex(8)}"
        youtube_url = f"https://www.youtube.com/embed/{video_id}"

        try:
            await client.add_widget(
                room_id=room_id,
                widget_id=widget_id,
                widget_type="video",
                url=youtube_url,
                name=f"YouTube: {video_id}",
            )

            yield event.plain_result(
                f"已添加 YouTube 视频小组件\n"
                f"视频 ID: {video_id}\n"
                f"Widget ID: `{widget_id}`"
            )

        except Exception as e:
            logger.error(f"添加 YouTube 小组件失败: {e}")
            yield event.plain_result(f"添加 YouTube 小组件失败: {e}")

    @widget_group.command("custom")
    async def widget_custom(
        self,
        event: AstrMessageEvent,
        widget_id: str,
        name: str,
        url: str,
        widget_type: str = "customwidget",
    ):
        """添加自定义小组件（可指定 ID）

        用法: /widget custom <widget_id> <名称> <URL> [类型]

        参数:
            widget_id: 自定义小组件 ID
            name: 小组件显示名称
            url: 小组件 URL
            widget_type: 小组件类型 (默认: customwidget)

        URL 模板变量:
            $matrix_room_id - 当前房间 ID
            $matrix_user_id - 当前用户 ID
            $matrix_display_name - 用户显示名称

        示例:
            /widget custom mywidget "我的工具" "https://example.com?room=$matrix_room_id"
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        room_id = event.get_session_id()

        try:
            result = await client.add_widget(
                room_id=room_id,
                widget_id=widget_id,
                widget_type=widget_type,
                url=url,
                name=name,
            )

            yield event.plain_result(
                f"已添加自定义小组件 **{name}**\n"
                f"ID: `{widget_id}`\n"
                f"类型: {widget_type}\n"
                f"URL: {url}"
            )

        except Exception as e:
            logger.error(f"添加自定义小组件失败: {e}")
            yield event.plain_result(f"添加自定义小组件失败: {e}")
