import collections
import enum


class Service(enum.Enum):

    GITHUB = 'github'
    LASTPASS = 'lastpass'
    SLACK = 'slack'
    TRELLO = 'trello'


Account = collections.namedtuple(
    'Account',
    [
        'uid',  # uuid
        'creation_date',  # datetime
        'deactivation_date',  # datetime

        'username',  # Text
        'displayname',  # Text
        'email',  # Ascii
        'fixed_line',  # Ascii
        'mobile_line',  # Ascii

        'owned_groups',  # [group_uid]
        'groups',  # [group_uid]

        'external_uids',  # {service_code: uid}
    ],
)


Group = collections.namedtuple(
    'Group',
    [
        'uid',  # uuid
        'creation_date',  # datetime
        'deactivation_date',  # datetime

        'name',  # ascii
        'description',  # Text
    ],
)
