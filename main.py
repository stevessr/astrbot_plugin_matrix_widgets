"""
Matrix Widgets Plugin - 提供 Matrix 小组件管理命令

此插件依赖于 astrbot_plugin_matrix_adapter 提供的 Matrix 客户端。
"""

import secrets
import urllib.parse
from typing import TYPE_CHECKING

import aiohttp

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

if TYPE_CHECKING:
    from astrbot_plugin_matrix_adapter.client import MatrixHTTPClient


class Main(Star):
    def __init__(self, context: Context) -> None:
        super().__init__(context)
        self.context = context
        # 存储每个用户的搜索结果缓存
        self._music_cache: dict[str, list[dict]] = {}
        # 存储每个用户的输出模式偏好 (widget/link)
        self._music_mode: dict[str, str] = {}

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
            logger.debug(f"获取 Matrix 客户端失败：{e}")

        return None

    @filter.command_group("widget")
    def widget_group(self):
        """Matrix 小组件管理命令"""

    @widget_group.command("list")
    async def widget_list(self, event: AstrMessageEvent):
        """列出当前房间的所有小组件

        用法：/widget list
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
                lines.append(f"  类型：{widget_type}")
                lines.append(f"  URL: {url[:50]}..." if len(url) > 50 else f"  URL: {url}")
                lines.append(f"  创建者：{creator}")
                lines.append("")

            yield event.plain_result("\n".join(lines))

        except Exception as e:
            logger.error(f"获取小组件列表失败：{e}")
            yield event.plain_result(f"获取小组件列表失败：{e}")

    @widget_group.command("add")
    async def widget_add(self, event: AstrMessageEvent, name: str, url: str, widget_type: str = "customwidget"):
        """添加小组件到当前房间

        用法：/widget add <名称> <URL> [类型]

        参数：
            name: 小组件显示名称
            url: 小组件 URL
            widget_type: 小组件类型 (默认：customwidget)

        示例：
            /widget add "我的网页" https://example.com
            /widget add "Jitsi 会议" https://meet.jit.si/myroom jitsi
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
                f"类型：{widget_type}\n"
                f"URL: {url}"
            )

        except Exception as e:
            logger.error(f"添加小组件失败：{e}")
            yield event.plain_result(f"添加小组件失败：{e}")

    @widget_group.command("remove")
    async def widget_remove(self, event: AstrMessageEvent, widget_id: str):
        """从当前房间移除小组件

        用法：/widget remove <widget_id>

        参数：
            widget_id: 小组件 ID (可通过 /widget list 查看)

        示例：
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
            logger.error(f"移除小组件失败：{e}")
            yield event.plain_result(f"移除小组件失败：{e}")

    @widget_group.command("jitsi")
    async def widget_jitsi(self, event: AstrMessageEvent, room_name: str = ""):
        """快速添加 Jitsi 视频会议小组件

        用法：/widget jitsi [房间名]

        参数：
            room_name: Jitsi 房间名 (可选，默认自动生成)

        示例：
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
                f"会议链接：{jitsi_url}\n"
                f"Widget ID: `{widget_id}`"
            )

        except Exception as e:
            logger.error(f"添加 Jitsi 小组件失败：{e}")
            yield event.plain_result(f"添加 Jitsi 小组件失败：{e}")

    @widget_group.command("etherpad")
    async def widget_etherpad(self, event: AstrMessageEvent, pad_name: str = ""):
        """快速添加 Etherpad 协作文档小组件

        用法：/widget etherpad [文档名]

        参数：
            pad_name: Etherpad 文档名 (可选，默认自动生成)

        示例：
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
                f"文档链接：{etherpad_url}\n"
                f"Widget ID: `{widget_id}`"
            )

        except Exception as e:
            logger.error(f"添加 Etherpad 小组件失败：{e}")
            yield event.plain_result(f"添加 Etherpad 小组件失败：{e}")

    @widget_group.command("youtube")
    async def widget_youtube(self, event: AstrMessageEvent, video_id: str):
        """添加 YouTube 视频小组件

        用法：/widget youtube <视频 ID 或 URL>

        参数：
            video_id: YouTube 视频 ID 或完整 URL

        示例：
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
            logger.error(f"添加 YouTube 小组件失败：{e}")
            yield event.plain_result(f"添加 YouTube 小组件失败：{e}")

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

        用法：/widget custom <widget_id> <名称> <URL> [类型]

        参数：
            widget_id: 自定义小组件 ID
            name: 小组件显示名称
            url: 小组件 URL
            widget_type: 小组件类型 (默认：customwidget)

        URL 模板变量：
            $matrix_room_id - 当前房间 ID
            $matrix_user_id - 当前用户 ID
            $matrix_display_name - 用户显示名称

        示例：
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
                f"类型：{widget_type}\n"
                f"URL: {url}"
            )

        except Exception as e:
            logger.error(f"添加自定义小组件失败：{e}")
            yield event.plain_result(f"添加自定义小组件失败：{e}")

    # ==================== 音乐点歌功能 ====================

    @filter.command_group("music")
    def music_group(self):
        """音乐点歌命令组"""

    async def _search_netease(self, keyword: str) -> list[dict]:
        """网易云音乐搜索"""
        url = "https://music.163.com/api/search/get/web"
        params = {
            "s": keyword,
            "type": 1,
            "offset": 0,
            "limit": 10,
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://music.163.com/",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=params, headers=headers) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    songs = data.get("result", {}).get("songs", [])
                    return [
                        {
                            "id": str(song["id"]),
                            "name": song["name"],
                            "artist": "/".join(a["name"] for a in song.get("artists", [])),
                            "album": song.get("album", {}).get("name", ""),
                            "platform": "netease",
                            "url": f"https://music.163.com/#/song?id={song['id']}",
                            "embed_url": f"https://music.163.com/outchain/player?type=2&id={song['id']}&auto=1&height=66",
                        }
                        for song in songs
                    ]
        except Exception as e:
            logger.error(f"网易云音乐搜索失败：{e}")
            return []

    async def _search_qq(self, keyword: str) -> list[dict]:
        """QQ 音乐搜索"""
        url = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
        params = {
            "w": keyword,
            "format": "json",
            "p": 1,
            "n": 10,
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://y.qq.com/",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    songs = data.get("data", {}).get("song", {}).get("list", [])
                    return [
                        {
                            "id": song["songmid"],
                            "name": song["songname"],
                            "artist": "/".join(s["name"] for s in song.get("singer", [])),
                            "album": song.get("albumname", ""),
                            "platform": "qq",
                            "url": f"https://y.qq.com/n/ryqq/songDetail/{song['songmid']}",
                            "embed_url": f"https://i.y.qq.com/v8/playsong.html?songmid={song['songmid']}&type=0",
                        }
                        for song in songs
                    ]
        except Exception as e:
            logger.error(f"QQ 音乐搜索失败：{e}")
            return []

    async def _search_youtube(self, keyword: str) -> list[dict]:
        """YouTube 音乐搜索 (使用 Invidious API)"""
        # 使用公共 Invidious 实例进行搜索
        url = "https://inv.nadeko.net/api/v1/search"
        params = {
            "q": keyword,
            "type": "video",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return [
                        {
                            "id": video["videoId"],
                            "name": video["title"],
                            "artist": video.get("author", ""),
                            "album": "",
                            "platform": "youtube",
                            "url": f"https://www.youtube.com/watch?v={video['videoId']}",
                            "embed_url": f"https://www.youtube.com/embed/{video['videoId']}",
                        }
                        for video in data[:10]
                        if video.get("type") == "video"
                    ]
        except Exception as e:
            logger.error(f"YouTube 搜索失败：{e}")
            return []

    async def _search_spotify(self, keyword: str) -> list[dict]:
        """Spotify 搜索 (使用公开 embed 链接)"""
        # Spotify 不提供公开 API，使用搜索结果页面
        # 这里只提供直接输入 track ID 的方式
        # 如果输入看起来像 Spotify URL 或 track ID，直接返回
        track_id = None
        if "spotify.com/track/" in keyword:
            track_id = keyword.split("spotify.com/track/")[1].split("?")[0]
        elif len(keyword) == 22 and keyword.isalnum():
            track_id = keyword

        if track_id:
            return [
                {
                    "id": track_id,
                    "name": f"Spotify Track: {track_id}",
                    "artist": "",
                    "album": "",
                    "platform": "spotify",
                    "url": f"https://open.spotify.com/track/{track_id}",
                    "embed_url": f"https://open.spotify.com/embed/track/{track_id}",
                }
            ]
        return []

    def _format_search_results(self, songs: list[dict], platform: str) -> str:
        """格式化搜索结果"""
        if not songs:
            return f"未找到相关歌曲 ({platform})"

        lines = [f"**{platform} 搜索结果:**\n"]
        for i, song in enumerate(songs, 1):
            artist = f" - {song['artist']}" if song["artist"] else ""
            album = f" [{song['album']}]" if song["album"] else ""
            lines.append(f"{i}. **{song['name']}**{artist}{album}")

        lines.append("\n使用 `/music play <序号>` 播放歌曲")
        lines.append("使用 `/music mode widget|link` 切换输出模式")
        return "\n".join(lines)

    @music_group.command("netease")
    async def music_netease(self, event: AstrMessageEvent, keyword: str):
        """网易云音乐搜索

        用法：/music netease <关键词>

        示例：
            /music netease 周杰伦 稻香
        """
        user_id = event.get_sender_id()
        songs = await self._search_netease(keyword)
        self._music_cache[user_id] = songs
        yield event.plain_result(self._format_search_results(songs, "网易云音乐"))

    @music_group.command("qq")
    async def music_qq(self, event: AstrMessageEvent, keyword: str):
        """QQ 音乐搜索

        用法：/music qq <关键词>

        示例：
            /music qq 林俊杰 江南
        """
        user_id = event.get_sender_id()
        songs = await self._search_qq(keyword)
        self._music_cache[user_id] = songs
        yield event.plain_result(self._format_search_results(songs, "QQ 音乐"))

    @music_group.command("youtube")
    async def music_youtube(self, event: AstrMessageEvent, keyword: str):
        """YouTube 音乐搜索

        用法：/music youtube <关键词>

        示例：
            /music youtube lofi hip hop
        """
        user_id = event.get_sender_id()
        songs = await self._search_youtube(keyword)
        self._music_cache[user_id] = songs
        yield event.plain_result(self._format_search_results(songs, "YouTube"))

    @music_group.command("spotify")
    async def music_spotify(self, event: AstrMessageEvent, track_id_or_url: str):
        """Spotify 播放

        用法：/music spotify <track ID 或 URL>

        示例：
            /music spotify 4uLU6hMCjMI75M1A2tKUQC
            /music spotify https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC
        """
        user_id = event.get_sender_id()
        songs = await self._search_spotify(track_id_or_url)
        if songs:
            self._music_cache[user_id] = songs
            yield event.plain_result(
                f"已识别 Spotify 曲目\n"
                f"使用 `/music play 1` 播放\n"
                f"链接：{songs[0]['url']}"
            )
        else:
            yield event.plain_result(
                "请提供 Spotify Track ID 或完整 URL\n"
                "示例：/music spotify 4uLU6hMCjMI75M1A2tKUQC"
            )

    @music_group.command("mode")
    async def music_mode(self, event: AstrMessageEvent, mode: str):
        """切换点歌输出模式

        用法：/music mode <widget|link>

        参数：
            mode: 输出模式
                - widget: 添加为房间小组件 (默认)
                - link: 直接发送播放链接

        示例：
            /music mode widget
            /music mode link
        """
        user_id = event.get_sender_id()
        if mode not in ("widget", "link"):
            yield event.plain_result("模式必须是 `widget` 或 `link`")
            return

        self._music_mode[user_id] = mode
        mode_name = "小组件模式" if mode == "widget" else "链接模式"
        yield event.plain_result(f"已切换到 **{mode_name}**")

    @music_group.command("play")
    async def music_play(self, event: AstrMessageEvent, index: int):
        """播放搜索结果中的歌曲

        用法：/music play <序号>

        示例：
            /music play 1
        """
        user_id = event.get_sender_id()
        songs = self._music_cache.get(user_id, [])

        if not songs:
            yield event.plain_result("请先搜索歌曲，例如：`/music netease 周杰伦`")
            return

        if index < 1 or index > len(songs):
            yield event.plain_result(f"请输入 1-{len(songs)} 之间的序号")
            return

        song = songs[index - 1]
        mode = self._music_mode.get(user_id, "widget")

        if mode == "link":
            # 链接模式：直接发送播放链接
            platform_names = {
                "netease": "网易云音乐",
                "qq": "QQ 音乐",
                "youtube": "YouTube",
                "spotify": "Spotify",
            }
            platform_name = platform_names.get(song["platform"], song["platform"])
            yield event.plain_result(
                f"**{song['name']}**\n"
                f"歌手：{song['artist']}\n"
                f"平台：{platform_name}\n"
                f"链接：{song['url']}"
            )
        else:
            # 小组件模式：添加播放器小组件
            client = self._get_matrix_client(event)
            if not client:
                # 非 Matrix 平台时回退到链接模式
                yield event.plain_result(
                    f"**{song['name']}** - {song['artist']}\n"
                    f"链接：{song['url']}"
                )
                return

            room_id = event.get_session_id()
            widget_id = f"music_{song['platform']}_{secrets.token_hex(8)}"

            try:
                await client.add_widget(
                    room_id=room_id,
                    widget_id=widget_id,
                    widget_type="customwidget",
                    url=song["embed_url"],
                    name=f"♪ {song['name']} - {song['artist']}",
                )

                yield event.plain_result(
                    f"已添加音乐小组件\n"
                    f"**{song['name']}** - {song['artist']}\n"
                    f"Widget ID: `{widget_id}`"
                )
            except Exception as e:
                logger.error(f"添加音乐小组件失败：{e}")
                # 失败时回退到链接模式
                yield event.plain_result(
                    f"添加小组件失败，发送链接:\n"
                    f"**{song['name']}** - {song['artist']}\n"
                    f"链接：{song['url']}"
                )

    @music_group.command("search")
    async def music_search(self, event: AstrMessageEvent, keyword: str, platform: str = "netease"):
        """统一音乐搜索

        用法：/music search <关键词> [平台]

        参数：
            keyword: 搜索关键词
            platform: 平台 (netease/qq/youtube，默认 netease)

        示例：
            /music search 周杰伦
            /music search Taylor Swift youtube
        """
        user_id = event.get_sender_id()

        platform = platform.lower()
        if platform in ("netease", "163", "网易"):
            songs = await self._search_netease(keyword)
            platform_name = "网易云音乐"
        elif platform in ("qq", "qqmusic", "腾讯"):
            songs = await self._search_qq(keyword)
            platform_name = "QQ 音乐"
        elif platform in ("youtube", "yt", "ytb"):
            songs = await self._search_youtube(keyword)
            platform_name = "YouTube"
        else:
            yield event.plain_result(
                f"不支持的平台：{platform}\n"
                "支持的平台：netease, qq, youtube"
            )
            return

        self._music_cache[user_id] = songs
        yield event.plain_result(self._format_search_results(songs, platform_name))
