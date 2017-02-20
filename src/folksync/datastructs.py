import collections
import enum


class Service(enum.Enum):

    GITHUB = 'github'
    LASTPASS = 'lastpass'
    SLACK = 'slack'
    TRELLO = 'trello'


class Type(enum.Enum):
    INTERNAL = 'internal'
    CONTRACTOR = 'contractor'
    EXTERNAL = 'external'


Account = collections.namedtuple(
    'Account',
    [
        'hrid',  # unique ID
        'uuid',  # uuid
        'creation_date',  # datetime
        'deactivation_date',  # datetime

        'type',  # Type

        'username',  # Text
        'firstname',  # Text
        'lastname',  # Text
        'displayname',  # Text
        'email',  # Ascii
        'fixed_line',  # Ascii
        'mobile_line',  # Ascii

        'external_uids',  # {service_code: uid}
    ],
)


Group = collections.namedtuple(
    'Group',
    [
        'hrid',  # unique ID
        'uuid',  # uuid
        'creation_date',  # datetime
        'deactivation_date',  # datetime

        'name',  # ascii
        'description',  # Text

        'owners',  # [uid]
        'members',  # [uid]
    ],
)
