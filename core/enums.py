from enum import IntEnum, Enum


class Color(IntEnum):
    GRAY = 0x2F3136
    GREEN = 0x00FF00
    RED = 0xFF0000
    BLUE = 0x0000FF


class ClientInfo(IntEnum):
    ZONYX = 397414803473170432
    BOT_GUILD_ID = 0