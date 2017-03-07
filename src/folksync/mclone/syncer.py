import collections

from .datastructs import Action, Change, ReplicationRun
from .datastructs import ReplicationContext, ReplicationMode, ReplicationStep, ReplicationEvent


def replicate(source_data, remote_data, mapper, keys):

    stats = {action: set() for action in Action}
    changes = {action: {} for action in Action}

    for key, default_action in sorted(keys.items()):

        source_item = source_data.get(key)
        sink_item = remote_data.get(key)

        # A source/sink may not provide empty items
        assert source_item is not None or sink_item is not None
        if default_action is not None:
            change = Change(
                action=default_action,
                key=key,
                target=source_item,
                previous=None,
                delta=None,
            )
        elif source_item is None:
            change = Change(
                action=Action.DELETED,
                key=key,
                target=source_item,
                previous=sink_item,
                delta=None,
            )
        else:
            delta = mapper(sink_item, source_item)
            if sink_item is None:
                action = Action.CREATED
            elif delta:
                action = Action.UPDATED
            else:
                action = Action.UNCHANGED

            change = Change(
                action=action,
                key=key,
                target=source_item,
                previous=sink_item,
                delta=delta,
            )

        changes[change.action][key] = change
        stats[change.action].add(key)
        # End `for key in keys`

    context = ReplicationContext(
        keys=keys,
        changes=changes,
        stats={action: len(stats[action]) for action in Action},
    )

    yield ReplicationEvent(
        step=ReplicationStep.NOTIFY,
        action=None,
        context=context,
    )
    mode = yield ReplicationEvent(
        step=ReplicationStep.CHOOSE_MODE,
        action=None,
        context=context,
    )
    assert mode in ReplicationMode  # Make sure the caller used .send(mode)

    MODE_ACTIONS = [
        (Action.CREATED, [ReplicationMode.ADDITIVE, ReplicationMode.FULL]),
        (Action.UPDATED, [ReplicationMode.ADDITIVE, ReplicationMode.FULL]),
        (Action.DELETED, [ReplicationMode.FULL]),
    ]

    for action, modes in MODE_ACTIONS:
        targets = changes[action]
        if not targets:
            step = ReplicationStep.EMPTY
        elif mode not in modes:
            step = ReplicationStep.SKIPPED
        else:
            step = ReplicationStep.EXEC

        yield ReplicationEvent(
            action=action,
            step=step,
            context=context,
        )


class Replicator:
    def __init__(self, source, sinks, interactor):
        self.source = source
        self.sinks = sinks
        self.interactor = interactor

    def replicate(self, mode, only_keys=()):
        source_data = self.source.all()

        for sink in self.sinks:
            sink_data = sink.all()

            # Process all keys (local + remote)
            keys = {
                key: None if key in only_keys or not only_keys else Action.SKIPPED
                for key in set(source_data.keys()) | set(sink_data.keys())
            }

            for key in sink.get_skipped_keys(keys):
                keys[key] = Action.SKIPPED

            sink_replication = replicate(
                source_data=source_data,
                remote_data=sink_data,
                mapper=sink.merge,
                keys=keys,
            )
            run = ReplicationRun(
                source=self.source,
                sink=sink,
                mode=mode,
            )

            reply = None
            try:
                while True:
                    event = sink_replication.send(reply)
                    reply = self.interactor(event, run)
                    self.maybe_act(event, run)

            except StopIteration:
                pass

    def maybe_act(self, event, run):
        if event.step is not ReplicationStep.EXEC:
            return

        handlers = {
            Action.CREATED: run.sink.create_batch,
            Action.UPDATED: run.sink.update_batch,
            Action.DELETED: run.sink.delete_batch,
        }

        handlers[event.action](changes=event.context.changes[event.action])
