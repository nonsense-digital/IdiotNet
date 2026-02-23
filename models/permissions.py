# module that defines a bunch of enums
# once again, to avoid python's stupid circular imports
from enum import Enum

# this enum represents different punishments (or the lack of) that can be added to a users
class PunishmentType(Enum):
    # no punishment, regular status
    NONE = "none"
    # temporary punishment that limits certain user interactions such as posting and commenting
    MUTE = "mute"
    # temporary punishment that limits all user activity
    BAN = "ban"
    # permanent punishment that deletes all user content and makes account unusable
    PERMABAN = "permaban"

class Role(str, Enum):
    # unverified, can't do anything
    UNVERIFIED = "unverified"
    # base role, can post, comment, follow, like, etc
    MEMBER = 'member'
    # higher role, can manage punishments, censor content, and track user IP addresses
    MODERATOR = 'moderator'
    # highest role, can change server configuration and promote users (dangerous)
    ADMIN = 'admin'

    # get an integer that represents the permission level
    @property
    def level(self):
        return list(self.__class__).index(self)