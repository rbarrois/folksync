import collections
import enum


class ObjectKind(enum.Enum):
    ACCOUNT = 'account'
    GROUP = 'group'


class Service(enum.Enum):

    GITHUB = 'github'
    LASTPASS = 'lastpass'
    SLACK = 'slack'
    TRELLO = 'trello'


class Type(enum.Enum):
    INTERNAL = 'internal'
    CONTRACTOR = 'contractor'
    EXTERNAL = 'external'


AccountUID = collections.namedtuple(
    'AccountUID',
    [
        'hrid',  # source-side human readable ID; may change
        'uuid',  # uuid; may not change
        'username',  # ascii; may change
        'email',  # ascii; may change
    ],
)


Account = collections.namedtuple(
    'Account',
    [
        'uids',  # Unique IDs: an AccountUID record
        'creation_date',  # datetime
        'deactivation_date',  # datetime

        'type',  # Type

        'firstname',  # Text
        'lastname',  # Text
        'displayname',  # Text
        'fixed_line',  # Ascii
        'mobile_line',  # Ascii

        'external_uids',  # {service_code: uid}
    ],
)


GroupUID = collections.namedtuple(
    'GroupUID',
    [
        'hrid',  # source-side human readable ID; may change
        'uuid',  # uuid; may not change
        'name',  # ascii; may change
    ],
)


Group = collections.namedtuple(
    'Group',
    [
        'uids',  # Unique IDs: a GroupUID record
        'creation_date',  # datetime
        'deactivation_date',  # datetime

        'description',  # Text

        'owners',  # [uid]
        'members',  # [uid]
    ],
)


UID_FIELDS = {
    ObjectKind.ACCOUNT: AccountUID._fields,
    ObjectKind.GROUP: GroupUID._fields,
}
