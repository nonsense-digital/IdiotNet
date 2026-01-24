# module that defines a bunch of enums
# once again, to avoid python's stupid circular imports
from enum import Enum

# thanks for the help on enums from https://typing.python.org/en/latest/spec/enums.html
# and also https://stackoverflow.com/questions/43202777/get-enum-name-from-multiple-values-python
# this enum represents different punishments (or the lack of) that can be added to a users
class PunishmentType(Enum):
    # (value: str, warning: str)
    NONE = ("none", "")
    # temporary punishment that limits certain user interactions such as posting and commenting
    MUTE = ("mute", "The user will be unable to comment, post, change their bio, or perform any website action other than viewing content.")
    # temporary punishment that limits all user activity
    BAN = ("ban", "The user will be unable to use any website functions while logged in.")
    # permanent punishment that deletes all user content and makes account unusable
    PERMABAN = ("permaban", "The user will be unable to use any website functions while logged in, and all of their data will be removed.")

    def __new__(cls, *values):
        obj = object.__new__(cls)
        # first value is canonical value
        obj._value_ = values[0]
        for other_value in values[1:]:
            cls._value2member_map_[other_value] = obj
        obj._all_values = values
        return obj

    def __init__(self, value, warning):
        self._value_ = value
        self.warning = warning

    @property
    def title(self):
        return self.name.capitalize()

class Role(str, Enum):
    MEMBER = 'member'
    MODERATOR = 'moderator'
    ADMIN = 'admin'