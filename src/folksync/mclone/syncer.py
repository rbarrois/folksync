import collections

from .datastructs import Action, Change, ReplicationContext, ReplicationMode, ReplicationStepState


def replicate(self, source_data, remote_data, mapper, mode, only_keys=()):

    stats = {action: set() for action in Action}

    changes = {action: {} for action in Action}

    # Process all keys (local + remote)
    base_keys = set(source_data.keys()) | set(remote_data.keys())
    if only_keys:
        keys = base_keys & set(only_keys)
    else:
        keys = base_keys
    sink_skips = sink.get_skipped_keys(keys)

    for key in keys:

        source_item = source_data.get(key)
        sink_item = remote_data.get(key)

        # A source/sink may not provide empty items
        assert source_item is not None or sink_item is not None
        if key in sink_skips:
            change = Change(
                action=Action.SKIPPED,
                key=key,
                sink=sink,
                target=source_item,
                previous=None,
                delta=None,
            )
        elif source_item is None:
            change = Change(
                action=Action.DELETED,
                key=key,
                sink=sink,
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
                sink=sink,
                target=source_item,
                previous=sink_item,
                delta=delta,
            )

        changes[change.action][key] = change
        stats[change.action].add(key)
        # End `for key in keys`

    context = ReplicationContext(
        keys=set(source_data.keys()),
        changes=changes,
        stats={action: len(stats[action]) for action in Action},
    )

    yield NOTIF_CHANGES
    mode = yield CHOOSE_MODE(context, mode)

    MODE_ACTIONS = [
        (Action.CREATED, [ReplicationMode.ADDITIVE, ReplicationMode.FULL]),
        (Action.UPDATED, [ReplicationMode.ADDITIVE, ReplicationMode.FULL]),
        (Action.DELETED, [ReplicationMode.FULL]),
    ]

    for action, modes in Action:
        targets = changes[action]
        if not targets:
            state = ReplicationStepState.EMPTY
        elif mode not in modes:
            state = ReplicationStepState.SKIPPED
        else:
            state = ReplicationStepState.EXEC

        yield ReplicationStep(
            sink=sink,
            action=action,
            changes=targets,
            state=state,
            context=context,
        )
