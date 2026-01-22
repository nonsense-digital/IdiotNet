# module that defines a bunch of enums
# once again, to avoid python's stupid circular imports
from enum import Enum
class PunishmentType(Enum):
    NONE = "none"
    MUTE = "mute"
    BAN = "ban"
    PERMABAN = "permaban"

class Role(str, Enum):
    MEMBER = 'member'
    MODERATOR = 'moderator'
    ADMIN = 'admin'