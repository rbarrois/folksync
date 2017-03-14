import time

import apiclient.discovery
import httplib2
import oauth2client.service_account

from .. import datastructs


SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user.readonly',
    'https://www.googleapis.com/auth/admin.directory.group.readonly',
    'https://www.googleapis.com/auth/admin.directory.group.member.readonly',
]

#: Maximum batch size
#: See https://developers.google.com/api-client-library/python/guide/batch
BATCH_MAX_SIZE = 50
BATCH_QPS = 10


def unroll(endpoint, request, field):
    while request is not None:
        response = request.execute()
        yield from response[field]
        request = endpoint.list_next(request, response)


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
    def to_folksync_uids(cls, user):
        """Extract UIDs from a GSuite user object."""
        def get_entry(entries, **kwargs):
            for entry in entries:
                for key, value in kwargs.items():
                    if entry.get(key) != value:
                        break
                return entry

        return datastructs.AccountUID(
            hrid=get_entry(user.get('externalIds', {}), type='custom', customType='hrid'),
            uuid=get_entry(user.get('externalIds', {}), type='custom', customType='uuid'),
            username=get_entry(user.get('externalIds', {}), type='account'),
            email=user['primaryEmail'],
        )

    @classmethod
    def merge(cls, remote, local):
        if remote is None:
            remote = {}
        phones = []
        if local.mobile_line:
            phones.append({
                'type': 'work_mobile',
                'value': local.mobile_line,
            })
        if local.fixed_line:
            phones.append({
                'type': 'work',
                'value': local.fixed_line,
            })

        external_ids = [
            {
                'type': 'custom',
                'customType': 'UUID',
                'value': local.uids.uuid,
            },
            {
                'type': 'custom',
                'customType': 'hrid',
                'value': local.uids.hrid,
            },
            {
                'type': 'account',
                'value': local.uids.username,
            },
        ]

        # XXX: GSuite might have extra emails, we'll have to fix this
        emails = [
            {
                'primary': True,
                'address': local.uids.email,
            },
        ]

        new_remote = remote.copy() if remote else {}
        new_remote.update({
            # 'aliases': [],  # FIXME: Store in the directory
            'emails': emails,
            'externalIds': external_ids,
            # 'hashFunction': 'MD5',  # FIXME: Use a password
            'name': {
                'givenName': local.firstname,
                'familyName': local.lastname,
                'fullName': local.displayname,
            },
            # 'password': local.password,  # FIXME: Use a password
            'phones': phones or None,
            'primaryEmail': local.uids.email,
            'suspended': local.deactivation_date is not None,
        })
        delta = {
            key: value
            for key, value in new_remote.items()
            if value != remote.get(key)
        }
        if delta:
            return {
                'prev': {key: remote.get(key) for key in delta},
                'new': delta,
            }
        return delta

    def fetch(self):
        endpoint = self.client.users()
        request = endpoint.list(domain='polyconseil.fr')
        yield from unroll(endpoint, request, 'users')

    def all(self):
        items = self.fetch()
        return {
            self.to_folksync_uids(obj): obj
            for obj in items
        }

    def create_batch(self, changes):
        pass

    def update_batch(self, changes):
        pass

    def delete_batch(self, changes):
        pass


class GSuiteGroupAPI:
    def __init__(self, client):
        self.client = client

    @classmethod
    def to_folksync_uids(cls, group):
        """Extract UIDs from a GSuite user object."""
        return datastructs.GroupUID(
            hrid=None,
            uuid=None,
            name=(group['name'] or group['email']).split('@')[0],
        )

    @classmethod
    def merge(cls, remote, local):
        if remote is None:
            remote = {}

        new_remote = remote.copy()
        new_remote.update({
            'description': local.description or '',
            'email': '%s@%s' % (local.uids.name.lower(), 'polyconseil.fr'),
            'members': local.members,
        })
        delta = {
            key: value
            for key, value in new_remote.items()
            if value != remote.get(key)
        }
        if delta:
            return {
                'prev': {key: remote.get(key) for key in delta},
                'new': delta,
            }
        return delta

    def fetch(self):
        g_endpoint = self.client.groups()
        m_endpoint = self.client.members()
        g_request = g_endpoint.list(domain='polyconseil.fr')
        groups = {g['id']: g for g in unroll(g_endpoint, g_request, 'groups')}

        pending = {
            gid: m_endpoint.list(groupKey=gid)
            for gid in sorted(groups)
        }

        def handle(gid, response, exception):
            print("Handling group %r / %r" % (gid, groups[gid]['email']))
            if exception is not None:
                raise exception

            request = pending.pop(gid)
            if response is None:
                return
            groups[gid].setdefault('members', []).extend([
                m['email'].lower() for m in response['members']
            ])
            if response.get('nextPageToken'):
                pending[gid] = m_endpoint.list_next(request, response)

        while pending:
            batch = self.client.new_batch_http_request(callback=handle)
            requests = sorted(pending.items())[:BATCH_MAX_SIZE]
            print("Sending batch of %d requests" % len(requests))
            for gid, request in requests:
                batch.add(request, request_id=gid)
            batch.execute()
            if pending:
                delay = len(requests) // BATCH_QPS + 1
                print("Waiting %ds" % delay)
                time.sleep(delay)

        yield from groups.values()

    def all(self):
        items = self.fetch()
        return {
            self.to_folksync_uids(obj): obj
            for obj in items
        }


class GSuiteSink:
    name = 'GSuite'

    def __init__(self, config):
        self.client_keyfile = config.getstr('gsuite.keyfile')
        self.client_impersonate = config.getstr('gsuite.impersonate')
        self.domain = config.getstr('gsuite.domain')
        self.client = None
        self.user_api = None
        self.group_api = None


    def _setup_client(self):
        credentials = oauth2client.service_account.ServiceAccountCredentials.from_json_keyfile_name(
            self.client_keyfile,
            SCOPES,
        )
        user_credentials = credentials.create_delegated(sub=self.client_impersonate)
        authenticated_http = user_credentials.authorize(httplib2.Http())
        return apiclient.discovery.build(
            serviceName='admin',
            version='directory_v1',
            http=authenticated_http,
        )

    def connect(self):
        self.client = self._setup_client()
        self.user_api = GSuiteUserAPI(self.client)
        self.group_api = GSuiteGroupAPI(self.client)

    def fetch(self, kind):
        if kind is datastructs.ObjectKind.ACCOUNT:
            return self.user_api.all()
        else:
            return self.group_api.all()

    def merger(self, kind):
        if kind is datastructs.ObjectKind.ACCOUNT:
            return self.user_api.merge
        else:
            return self.group_api.merge
