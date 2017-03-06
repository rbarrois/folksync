class GEntryDict:
    def __init__(self, initial=(), value_field='value'):
        self.entries = {}
        self.value_field = value_field
        for entry in initial:
            self.upsert(entry)

    def upsert(self, entry):
        key_parts = [
            (key, value)
            for key, value in entry.items()
            if key != self.value_field
        ]
        key = tuple(sorted(key_parts))
        self.entries[key] = entry

    def __iter__(self):
        for _key, value in sorted(self.entries.items()):
            yield value

    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            list(self),
        )


class GSuiteUserAPI:
    def __init__(self, client):
        self.client = client

    @classmethod
    def to_folksync(cls, user):
        """Extract fields from a GSuite user object."""
        def get_entry(entries, **kwargs):
            for entry in entries:
                for key, value in kwargs.items():
                    if entry.get(key) != value:
                        break
                return entry


        return datastructs.Account(
            hrid=get_entry(user['externalIds'], type='custom', customType='hrid'),
            uuid=get_entry(user['externalIds'], type='custom', customType='uuid'),
            creation_date=None,
            deactivation_date=None,
            type=None,
            username=get_entry(user['externalIds'], type='account'),
            firstname=None,
            lastname=None,
            email=user['primaryEmail'],
            fixed_line=None,
            mobile_line=None,
            external_uids=None,
        )

    @classmethod
    def merge(cls, remote, local):
        phones = []
        if local.mobile_line:
            phones.append({
                'primary': True,
                'type': 'work_mobile',
                'value': local.mobile_line,
            })
        if local.fixed_line:
            phones.append({
                'primary': False,
                'type': 'work',
                'value': local.fixed_line,
            })

        external_ids = [
            {
                'type': 'custom',
                'customType': 'UUID',
                'value': local.uuid,
            },
            {
                'type': 'custom',
                'customType': 'hrid',
                'value': local.hrid,
            },
            {
                'type': 'account',
                'value': local.username,
            },
        ]

        # XXX: GSuite might have extra emails, we'll have to fix this
        emails = [
            {
                'primary': True,
                'type': 'work',
                'address': local.mail,
            },
        ]

        new_remote = remote.copy()
        new_remote.update({
            # 'aliases': [],  # FIXME: Store in the directory
            'emails': emails,
            'externalIds': external_ids,
            'id': remote_id,
            # 'hashFunction': 'MD5',  # FIXME: Use a password
            'name': {
                'givenName': local.firstname,
                'familyName': local.lastname,
            },
            # 'password': local.password,  # FIXME: Use a password
            'phones': phones,
            'primaryEmail': local.mail,
            'suspended': now >= local.deactivation_date,
        })
        return new_remote

    def fetch(self):
        pass

    def all(self):
        return {
            self.to_folksync(obj): obj
            for obj in self.fetch()
        }

    def create_batch(self, changes):
        pass

    def update_batch(self, changes):
        pass

    def delete_batch(self, changes):
        pass


class GSuiteSink:
    def __init__(self):
        self.client = None
        self.user_api = None
        self.group_api = None

    def connect(self):
        self.client = 42
        self.user_api = GSuiteUserAPI(self.client)
        self.group_api = GSuiteGroupAPI(self.client)

    def fetch_users(self):
        return self.user_api.all()

    def fetch_groups(self):
        return self.group_api.all()

    @classmethod
    def map_user(cls, user):
        """Convert a folksync User datastruct to a gsuite-style attr dict"""
        pass

    @classmethod
    def map_group(cls, group):
        """Convert a folksync Group datastruct to a gsuite-style attr dict"""
        pass
