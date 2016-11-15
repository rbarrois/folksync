from .datastructs import Action, Change, ReplicationMode, ReplicationStepState


class Replicator:
    def __init__(self, source, sinks, interaction):
        self.source = source
        self.sinks = sinks
        self.interaction = interaction

    def replicate(self, mode):
        source_data = self.source.all()

        # changes is a list of (sink, sink_changes) tuples
        # Where sink_changes is a dict(key => Change)
        changes = []

        for sink in self.sinks:
            sink_data = sink.all()
            sink_skips = sink.get_skipped_keys()
            sink_changes = {
                Action.CREATED: {},
                Action.UPDATED: {},
                Action.SKIPPED: {},
                Action.UNCHANGED: {},
                Action.DELETED: {},
            }

            # Process all keys (local + remote)
            keys = set(source_data.keys()) | set(sink_data.keys())

            for key in keys:
                source_item = source_data.get(key)
                sink_item = sink_data.get(key)

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
                    delta = sink.merge(sink_item, source_item)
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

                sink_changes[change.action][key] = change
                # End `for key in keys`

            changes.append((sink, sink_changes))
            # End `for sink in self.sinks`

        self.interaction.notify_changes(changes)
        mode = self.interaction.choose_mode(mode)

        for sink, sink_changes in changes:
            created = sink_changes[Action.CREATED]
            updated = sink_changes[Action.UPDATED]
            deleted = sink_changes[Action.DELETED]

            self._run_step(
                sink=sink,
                action=Action.CREATED,
                handler=sink.create_batch,
                changes=created,
                condition=mode in [ReplicationMode.ADDITIVE, ReplicationMode.FULL],
            )

            self._run_step(
                sink=sink,
                action=Action.UPDATED,
                handler=sink.update_batch,
                changes=updated,
                condition=mode in [ReplicationMode.ADDITIVE, ReplicationMode.FULL],
            )

            self._run_step(
                sink=sink,
                action=Action.DELETED,
                handler=sink.delete_batch,
                changes=deleted,
                condition=mode in [ReplicationMode.FULL],
            )

    def _run_step(self, sink, action, handler, changes, condition):
        if not changes:
            self.interaction.notify_step(sink, action, ReplicationStepState.EMPTY)
        elif not condition:
            self.interaction.notify_step(sink, action, ReplicationStepState.UNCHANGED)
        else:
            self.interaction.notify_step(sink, action, ReplicationStepState.START)
            handler(changes)
            self.interaction.notify_step(sink, action, ReplicationStepState.SUCCESS)
