import requests

from .. import datastructs


API_BASE = 'https://api.trello.com/1/'
API_ORG_MEMBERS = 'organization/%s/members'


class TrelloSink:
    name = 'Trello'

    def __init__(self, config, cache=None):
        self.app_id = config.getstr('trello.app_id')
        self.auth_token = config.getstr('trello.auth_token')
        self.cache = cache['trello']
        self.teams = config.getlist('trello.teams')

    def connect(self):
        pass

    def _prepare(self, path, path_args, query):
        query = dict(query)
        query.update({'key': self.app_id, 'token': self.auth_token})
        path = API_BASE + path % path_args
        return path, query

    def _get(self, path, *path_args, **query):
        path, params = self._prepare(path, path_args, query)
        return requests.get(path, params=params)

    def _load_accounts(self):
        accounts = {}
        for team in self.teams:
            response = self._get(API_ORG_MEMBERS, team)
            for member in response.json():
                accounts[member['id']] = member

        return {
            self.to_folksync_uids(member): member
            for member in accounts.values()
        }

    def to_folksync_uids(self, member):
        cached_data = self.cache['trello:%s' % member['id']]
        if cached_data is None:
            return datastructs.AccountUID(
                hrid=None,
                uuid=None,
                username=member['username'],
                email=None,
            )
        return datastructs.AccountUID(
            hrid=cached_data['hrid'],
            uuid=cached_data['uuid'],
            username=cached_data['username'],
            email=cached_data['email'],
        )

    def fetch(self, kind):
        if kind is datastructs.ObjectKind.ACCOUNT:
            return self._load_accounts()
        else:
            pass

    def merge_account(self, remote, local):
        cached_data = self.cache['local:%s' % local.uids.uuid] or {}
        remote = remote or {}
        new_remote = remote.copy()
        new_remote.update({
            'id': cached_data.get('id'),
            'username': cached_data.get('username', local.uids.username),
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
        return {}

    def merger(self, kind):
        return self.merge_account
