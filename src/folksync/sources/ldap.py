
import collections
import enum
import ldap

from .. import datastructs


class FieldType(enum.Enum):
    TEXT = 0
    DATETIME = 1
    BYTES = 2


FieldFlags = collections.namedtuple('FieldFlags', ['decode', 'multi_valued'])


class LdapSource:
    def __init__(self, uri, base, filterstr, bind_dn, bind_pwd):
        self.uri = uri
        self.bind_dn = bind_dn
        self.bind_pwd = bind_pwd

        self.base = base
        self.filterstr = filterstr

        self.conn = None

    def connect(self):
        assert self.conn is None

        self.conn = ldap.initialize(
            uri=self.uri,
        )
        if self.bind_dn:
            self.conn.simple_bind_s(
                who=self.bind_dn,
                cred=self.bind_pwd,
            )

    def _extract_value(self, flags, values):
        if flags.type == FieldType.TEXT:
            values = [value.decode('utf-8') for value in values]

        elif flags.type == FieldType.DATETIME:
            values = [
                UTC.normalize(datetime.datetime.strptime('%Y%m%d%H%M%SZ', value.decode('utf-8')))
                for value in values
            ]

        # elif flags.type == FieldType.UUID:

        else:
            assert flags.type == FieldType.BYTES

        if flags.multi_valued:
            return values
        if not values or not values[0]:
            return None
        return values[0]

    def fetch_all(self, fields):
        results = self.conn.search_ext_s(
            base=self.base,
            scope=ldap.SCOPE_SUBTREE,
            filterstr=self.filterstr,
            attrlist=list(fields),
        )

        for dn, data in results:
            values = {
                field_name: self._extract_value(flags, data.get(field) or [])
                for field, flags in fields.items()
            }

            yield dn, values


class LdapUsers:
    def __init__(self, params):
        self.source = LdapSource(
            uri=params.uri,
            bind_dn=params.bind_dn,
            bind_pwd=params.bind_pwd,
            base=params.users_base,
            filterstr=params.filterstr,
        )

    FIELDS = {
        'uid': TextField(),
        'creation_date:' DateTimeField(),
        'deactivation_date': DateTimeField(),

        'mail:' FieldFlags(type=FieldType.TEXT, multi_valued=False),
    }

    def fetch_all(self):
        for dn, values in self.source.fetch_all(self.FIELDS):
            yield datastructs.Account(
                uid=dn,
                creation_date=None,
                deactivation_date=None,

                username=values['uid'],
                displayname=None,
                email=values['mail'],
                fixed_line=None,
                mobile_line=None,
                owned_groups=[],
                groups=[],
                external_uids={},
            )
