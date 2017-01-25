import logging
import sys

from .datastructs import Action, ReplicationMode, ReplicationStepState


class BaseDecider:
    def choose_mode(self, context, mode):
        return mode


class LogPrinter:
    def __init__(self, logname='folksync.mclone'):
        self.logger = logging.getLogger(logname)

    def display(self, message, ctxt):
        self.logger.info(message, ctxt or {})


class BaseInteractor:
    def __init__(self, *, printer=None, decider=None, **kwargs):
        self.printer = printer or LogPrinter()
        self.decider = decider or BaseDecider()

    def notify_changes(self, context):
        # changes is a list of {action => {key => change}} dicts
        if not context.changes:
            return
        self.printer.display(
            "Replicating %(total)d objects to %(sinks)d sinks: "
            "created=%(created)d, updated=%(updated)d, skipped=%(skipped)d, deleted=%(deleted)d",
            dict(
                total=len(context.keys),
                sinks=len(context.sinks),
                created=context.stats[Action.CREATED],
                skipped=context.stats[Action.SKIPPED],
                updated=context.stats[Action.UPDATED],
                deleted=context.stats[Action.DELETED],
            ),
        )

    def choose_mode(self, context, mode):
        new_mode = self.decider.choose_mode(context, mode)
        if new_mode == mode:
            self.printer.display(
                "Replicating in %(mode)s mode",
                dict(
                    mode=mode.name,
                ),
            )
        else:
            self.printer.display(
                "Switched mode from %(old)s to %(new)s",
                dict(
                    old=mode.name,
                    new=new_mode.name,
                ),
            )
        return new_mode

    def notify_step(self, sink, action, state, context):
        state_map = {
            ReplicationStepState.EMPTY: "Nothing to do",
            ReplicationStepState.SKIPPED: "Disabled",
            ReplicationStepState.START: "Start",
            ReplicationStepState.SUCCESS: "Success",
        }

        width = str(len(str(len(context.keys))))
        self.printer.display(
            "Sink %(sink)s: %(action)s %(items)" + width + "d items: " + state_map[state],
            dict(
                action=action.name,
                sink=sink,
                items=len(context.changes[sink][action]),
            ),
        )
        if state != ReplicationStepState.START:
            return
        changes = context.changes[sink][action]
        for key, change in sorted(changes.items()):
            self.printer.display(
                "Sink %(sink)s: %(action)s: %(key)s %(delta)s",
                dict(
                    sink=sink,
                    action=action.name,
                    key=change.key,
                    delta=change.delta,
                ),
            )


class ThresholdDecider(BaseDecider):
    def __init__(
            self, *,
            common_ratio=0.1, created_ratio=None, updated_ratio=None,
            skipped_ratio=None, deleted_ratio=None):
        self.ratios = {
            Action.CREATED: created_ratio or common_ratio,
            Action.UPDATED: updated_ratio or common_ratio,
            Action.SKIPPED: skipped_ratio or common_ratio,
            Action.DELETED: deleted_ratio or common_ratio,
        }

    def should_downgrade(self, context):
        total = len(context.keys)
        for action in Action:
            if action == Action.UNCHANGED:
                continue
            ratio = context.stats[action] / total
            if ratio > self.ratios[action]:
                return True
        return False

    def choose_mode(self, context, mode):
        if mode != ReplicationMode.DRY_RUN and self.should_downgrade(context):
            modes = list(ReplicationMode)
            return modes[modes.index(mode) - 1]
        return mode


class ShellDecider:
    def __init__(self, *, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin):
        self.stdout = stdout
        self.stderr = stderr
        self.stdin = stdin

    def _prompt(self, prompt, options):
        while True:
            self.stderr.write(prompt)
            choice = self.stdin.readline().strip()
            if choice in options:
                return choice
            self.stderr.write("Choice %r is not a valid option.\n\n" % choice)

    def choose_mode(self, context, mode):
        if mode == ReplicationMode.DRY_RUN:
            return mode

        options = {str(m.value): m for m in ReplicationMode}

        options_string = " ".join(
            ("[%d]/%s" if m == mode else "%d/%s") % (m.value, m.name)
            for m in ReplicationMode
        )
        prompt = "Choose mode: %s; enter to keep active mode\n" % options_string
        choice = self._prompt(prompt, [''] + list(sorted(options)))

        if choice == '':
            return mode

        return options[choice]
