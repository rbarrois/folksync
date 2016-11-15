import unittest

from mclone import base
from mclone import datastructs
from mclone import interaction
from mclone import syncer


class DictSource(base.DataSource):
    def __init__(self, data):
        self.data = data

    def all(self):
        return dict(self.data)


class DictSink(base.DataSink):
    def __init__(self, initial):
        self.initial = initial
        self.created = {}
        self.updated = {}
        self.deleted = []

    def all(self):
        base = dict(self.initial)
        base.update(self.created)
        base.update(self.updated)
        for k in self.deleted:
            base.pop(k)
        return base

    def merge(self, base, updated):
        if base == updated:
            return None
        else:
            return (base, updated)

    def create_batch(self, changes):
        for c in changes.values():
            assert c.key not in self.initial
            self.created[c.key] = c.target

    def update_batch(self, changes):
        for c in changes.values():
            assert self.initial[c.key] == c.previous
            assert c.key not in self.created
            self.updated[c.key] = c.target

    def delete_batch(self, changes):
        for c in changes.values():
            assert c.key in self.initial
            assert c.key not in self.deleted
            self.deleted.append(c.key)


class SyncTest(unittest.TestCase):

    def _replicate(self, source, sinks, mode):
        source = DictSource(source)
        sinks = [DictSink(sink) for sink in sinks]
        repl = syncer.Replicator(
            source=source,
            sinks=sinks,
            interaction=interaction.BaseInteraction(),
        )
        repl.replicate(mode)
        return sinks

    def test_full_create(self):
        sinks = self._replicate(
            source={'a': 1, 'b': 2},
            sinks=[{}, {}],
            mode=datastructs.ReplicationMode.ADDITIVE,
        )
        for sink in sinks:
            self.assertEqual({'a': 1, 'b': 2}, sink.created)
            self.assertEqual({}, sink.updated)
            self.assertEqual([], sink.deleted)

    def test_full_update(self):
        sinks = self._replicate(
            source={'a': 1, 'b': 2},
            sinks=[{'a': 3, 'b': 4}, {'a': 5, 'b': 6}],
            mode=datastructs.ReplicationMode.ADDITIVE,
        )
        for sink in sinks:
            self.assertEqual({}, sink.created)
            self.assertEqual({'a': 1, 'b': 2}, sink.updated)
            self.assertEqual([], sink.deleted)

    def test_full_delete(self):
        sinks = self._replicate(
            source={},
            sinks=[{'c': 3, 'd': 4}, {'c': 5, 'd': 6}],
            mode=datastructs.ReplicationMode.FULL,
        )
        for sink in sinks:
            self.assertEqual({}, sink.created)
            self.assertEqual({}, sink.updated)
            self.assertEqual(['c', 'd'], sorted(sink.deleted))

    def test_no_change(self):
        sinks = self._replicate(
            source={'a': 1, 'b': 2},
            sinks=[{'a': 1, 'b': 2}, {'a': 1, 'b': 2}],
            mode=datastructs.ReplicationMode.FULL,
        )
        for sink in sinks:
            self.assertEqual({}, sink.created)
            self.assertEqual({}, sink.updated)
            self.assertEqual([], sink.deleted)

    def test_mixed(self):
        sinks = self._replicate(
            source={'a': 1, 'b': 2},
            sinks=[{'b': 3, 'c': 4}, {'a': 2, 'd': 5}],
            mode=datastructs.ReplicationMode.FULL,
        )
        sink1, sink2 = sinks
        self.assertEqual({'a': 1}, sink1.created)
        self.assertEqual({'b': 2}, sink1.updated)
        self.assertEqual(['c'], sink1.deleted)

        self.assertEqual({'b': 2}, sink2.created)
        self.assertEqual({'a': 1}, sink2.updated)
        self.assertEqual(['d'], sink2.deleted)
