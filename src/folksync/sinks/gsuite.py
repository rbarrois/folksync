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
    USER_FIELDS = [
        'hrid',
        'uuid',
        'username',
        'firstname',
        'lastname',
        'email',
        'fixed_line',
        'mobile_line',
    ]

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
            firstname=user['name']['givenName'],
            lastname=user['name']['lastName'],
            email=user['primaryEmail'],
            fixed_line=get_entry(user['phones'], type='work'),
            mobile_line=get_entry(user['phones'], type='work_mobile'),
            external_uids={
                datastructs.Service.GSUITE: user['id'],
            },
        )

    @classmethod
    def from_folksync(cls, user, remote_id=None):
        phones = []
        if user.mobile_line:
            phones.append({
                'primary': True,
                'type': 'work_mobile',
                'value': user.mobile_line,
            })
        if user.fixed_line:
            phones.append({
                'primary': False,
                'type': 'work',
                'value': user.fixed_line,
            })

        external_ids = [
            {
                'type': 'custom',
                'customType': 'UUID',
                'value': user.uuid,
            },
            {
                'type': 'custom',
                'customType': 'hrid',
                'value': user.hrid,
            },
            {
                'type': 'account',
                'value': user.username,
            },
        ]

        # GSuite might have extra emails
        emails = [
            {
                'primary': True,
                'type': 'work',
                'address': user.mail,
            },
        ]

        return {
            # 'aliases': [],  # FIXME: Store in the directory
            'emails': emails,
            'externalIds': external_ids,
            'id': remote_id,
            # 'hashFunction': 'MD5',  # FIXME: Use a password
            'name': {
                'givenName': user.firstname,
                'familyName': user.lastname,
            },
            # 'password': user.password,  # FIXME: Use a password
            'phones': phones,
            'primaryEmail': user.mail,
            'suspended': now >= user.deactivation_date,
        }

    def create_batch(self, client, changes):
        pass

    def update_batch(self, client, changes):
        pass

    def delete_batch(self, client, changes):
        pass


class GSuiteSink:
    def connect(self):
        pass

    def fetch_users(self):
        pass

    def fetch_groups(self):
        pass

    @classmethod
    def map_user(cls, user):
        """Convert a folksync User datastruct to a gsuite-style attr dict"""
        pass

    @classmethod
    def map_group(cls, group):
        """Convert a folksync Group datastruct to a gsuite-style attr dict"""
        pass
