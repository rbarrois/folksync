import factory
import io

from mclone import base
from mclone import datastructs
from mclone import interaction
from mclone import syncer


class DictSource(base.DataSource):
    def __init__(self, data):
        self.data = data

    def all(self):
        return dict(self.data)

    def __repr__(self):
        return '<%s: data=%r>' % (self.__class__.__name__, self.data)


class DictSink(base.DataSink):
    def __init__(self, initial, name, skipped=()):
        self.initial = initial
        self.created = {}
        self.updated = {}
        self.deleted = []
        self.skipped = skipped
        self.name = name

    def get_skipped_keys(self, all_keys):
        return set(key for key in self.skipped if key in all_keys)

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

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)

    def __repr__(self):
        return '<%s %s: initial=%r skipped=%r>' % (
            self.__class__.__name__,
            self.name,
            self.initial,
            self.skipped,
        )


class ThresholDeciderFactory(factory.Factory):
    class Meta:
        model = interaction.ThresholdDecider

    common_ratio = 0.1


class ShellDeciderFactory(factory.Factory):
    class Meta:
        model = interaction.ShellDecider

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        kwargs['stdin'] = io.StringIO(''.join(
            l + '\n' for l in kwargs['stdin']
        ))
        return kwargs


class InteractorFactory(factory.Factory):
    class Meta:
        model = interaction.BaseInteractor


class DictSourceFactory(factory.Factory):
    class Meta:
        model = DictSource

    data = factory.Dict({})


class DictSinkFactory(factory.Factory):
    class Meta:
        model = DictSink

    initial = factory.Dict({})
    name = factory.Sequence(lambda i: 'sink%s' % i)


class ReplicatorFactory(factory.Factory):
    class Meta:
        model = syncer.Replicator

    sink0 = factory.SubFactory(DictSinkFactory)
    sink1 = factory.SubFactory(DictSinkFactory)

    source = factory.SubFactory(DictSourceFactory)
    interactor = factory.SubFactory(InteractorFactory)

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        sinks = [
            kwargs.pop(key) for key in sorted(kwargs) if key.startswith('sink')
        ]
        kwargs['sinks'] = sinks
        return kwargs
