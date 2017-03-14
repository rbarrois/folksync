import collections
import datetime
import enum
import ldap

from .. import datastructs


UTC = datetime.timezone.utc


class Ldap:
    def __init__(self, uri, bind_dn, bind_pwd):
        self.uri = uri
        self.bind_dn = bind_dn
        self.bind_pwd = bind_pwd

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

    def fetch(self, fields, filterstr, base):
        results = self.conn.search_ext_s(
            base=base,
            scope=ldap.SCOPE_SUBTREE,
            filterstr=filterstr,
            attrlist=list(fields),
        )

        for dn, data in results:
            values = {
                field_name: field.to_python(data.get(field_name) or [])
                for field_name, field in fields.items()
            }

            yield dn, values


class FieldType(enum.Enum):
    TEXT = 0
    DATETIME = 1
    TIMESTAMP = 2
    BYTES = 3
    IDENTIFIER = 4


class Field:
    def __init__(self, kind, multi_valued=False):
        self.kind = kind
        self.multi_valued = multi_valued
        assert kind in FieldType

    def to_python(self, values):
        if self.kind == FieldType.TEXT:
            values = [value.decode('utf-8') for value in values]

        elif self.kind == FieldType.IDENTIFIER:
            values = [value.decode('utf-8').lower() for value in values]

        elif self.kind == FieldType.DATETIME:
            values = [
                datetime.datetime.strptime(value.decode('utf-8'), '%Y%m%d%H%M%SZ').replace(tzinfo=UTC)
                for value in values
            ]
        elif self.kind == FieldType.TIMESTAMP:
            epoch = datetime.datetime.fromtimestamp(0).replace(tzinfo=UTC)
            values = [
                epoch + datetime.timedelta(days=int(value.decode('utf-8')))
                for value in values
            ]

        if self.multi_valued:
            return values
        elif values and values[0]:
            return values[0]
        else:
            return None


class OpenLdapSource:
    def __init__(self, config):
        self.config = config
        self.source = Ldap(
            uri=config.getstr('ldap.uri'),
            bind_dn=config.getstr('ldap.bind_dn'),
            bind_pwd=config.getstr('ldap.bind_pwd'),
        )
        self._user_emails = {}

    def connect(self):
        self.source.connect()

    USER_FIELDS = {
        'entryUUID': Field(FieldType.IDENTIFIER),
        'createTimestamp': Field(FieldType.DATETIME),
        'shadowExpire': Field(FieldType.TIMESTAMP),

        'uid': Field(FieldType.IDENTIFIER),  # username
        'givenName': Field(FieldType.TEXT),  # firstname
        'sn': Field(FieldType.TEXT),  # lastname
        'cn': Field(FieldType.TEXT),  # displayname
        'mail': Field(FieldType.IDENTIFIER),
        'telephoneNumber': Field(FieldType.TEXT),  # fixed_line
        'mobile': Field(FieldType.TEXT),
    }

    def fetch(self, kind):
        if kind is datastructs.ObjectKind.ACCOUNT:
            return self.fetch_users()
        else:
            return self.fetch_groups()

    def fetch_users(self):
        entries = self.source.fetch(
            fields=self.USER_FIELDS,
            base=self.config.getstr('ldap.users_base'),
            filterstr=self.config.getstr('ldap.users_filter'),
        )

        for dn, values in entries:
            self._user_emails[dn] = values['mail']

            yield datastructs.Account(
                uids=datastructs.AccountUID(
                    hrid=dn,
                    uuid=values['entryUUID'],
                    username=values['uid'],
                    email=values['mail'],
                ),
                creation_date=values['createTimestamp'],
                deactivation_date=values['shadowExpire'],

                type=datastructs.Type.INTERNAL,

                firstname=values['givenName'],
                lastname=values['sn'],
                displayname=values['cn'],
                fixed_line=values['telephoneNumber'],
                mobile_line=values['mobile'],
                external_uids={},
            )

    EXTUSER_FIELDS = {
        'mail': Field(FieldType.IDENTIFIER),
    }

    GROUP_FIELDS = {
        'entryUUID': Field(FieldType.IDENTIFIER),
        'cn': Field(FieldType.IDENTIFIER),
        'createTimestamp': Field(FieldType.DATETIME),
        'description': Field(FieldType.TEXT),
        'member': Field(FieldType.TEXT, multi_valued=True),
        'owner': Field(FieldType.TEXT, multi_valued=True),
    }

    def fetch_groups(self):
        # Load external accounts
        if self.config.getstr('ldap.extuser_base'):
            ext_entries = self.source.fetch(
                fields=self.EXTUSER_FIELDS,
                base=self.config.getstr('ldap.extuser_base'),
                filterstr=self.config.getstr('ldap.extuser_filter'),
            )
            for dn, values in ext_entries:
                self._user_emails[dn] = values['mail'].lower()

        entries = self.source.fetch(
            fields=self.GROUP_FIELDS,
            base=self.config.getstr('ldap.groups_base'),
            filterstr=self.config.getstr('ldap.groups_filter'),
        )

        for dn, values in entries:
            yield datastructs.Group(
                uids=datastructs.GroupUID(
                    hrid=dn,
                    uuid=values['entryUUID'],
                    name=values['cn'].lower(),
                ),
                creation_date=values['createTimestamp'],
                deactivation_date=None,
                description=values['description'],
                owners=values['owner'],
                members=sorted(
                    self._user_emails[v]
                    for v in values['member']
                    if v in self._user_emails
                ),
            )
