import json


class BaseCache:
    def __init__(self, config):
        pass

    def open(self):
        pass

    def commit(self):
        pass

    def __getitem__(self, domain):
        return SubCache(self, domain)

    def _get(self, key):
        raise NotImplementedError()

    def _set(self, key, value):
        raise NotImplementedError()

    def set(self, domain, key, value):
        self._set('%s.%s' % (domain, key), json.dumps(value))

    def get(self, domain, key):
        value = self._get('%s.%s' % (domain, key))
        return json.loads(value) if value is not None else None


class SubCache:
    def __init__(self, cache, domain):
        self.cache = cache
        self.domain = domain

    def __getitem__(self, key):
        return self.cache.get(self.domain, key)

    def __setitem__(self, key, value):
        return self.cache.set(self.domain, key, value)


class NullCache(BaseCache):
    def _set(self, key, value):
        pass

    def _get(self, key):
        return None


class FileCache(BaseCache):
    def __init__(self, config):
        super().__init__(config)
        self.path = config.getstr('cache.path')
        self.data = None

    def open(self):
        with open(self.path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def commit(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def set(self, domain, key, value):
        self.data.setdefault(domain, {})[key] = value

    def get(self, domain, key):
        return self.data.get(domain, {}).get(key)
