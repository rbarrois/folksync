import logging
import unittest

from mclone import base
from mclone import datastructs
from mclone import interaction
from mclone import syncer

from . import factories


class SyncTest(unittest.TestCase):
    no_logging = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if cls.no_logging:
            return
        root_logger = logging.getLogger()
        root_logger.addHandler(logging.StreamHandler())
        root_logger.setLevel(logging.INFO)

    def _replicate(self, mode, **kwargs):
        # Create a replicator, run it, return sinks.
        repl = factories.ReplicatorFactory(**kwargs)
        repl.replicate(mode)
        return repl.sinks

    # Normal operation
    # ================

    def test_full_create(self):
        sinks = self._replicate(
            source__data={'a': 1, 'b': 2},
            mode=datastructs.ReplicationMode.ADDITIVE,
        )
        for sink in sinks:
            self.assertEqual({'a': 1, 'b': 2}, sink.created)
            self.assertEqual({}, sink.updated)
            self.assertEqual([], sink.deleted)

    def test_full_update(self):
        sinks = self._replicate(
            source__data={'a': 1, 'b': 2},
            sink0__initial={'a': 3, 'b': 4},
            sink1__initial={'a': 5, 'b': 6},
            mode=datastructs.ReplicationMode.ADDITIVE,
        )
        for sink in sinks:
            self.assertEqual({}, sink.created)
            self.assertEqual({'a': 1, 'b': 2}, sink.updated)
            self.assertEqual([], sink.deleted)

    def test_full_delete(self):
        sinks = self._replicate(
            sink0__initial={'c': 3, 'd': 4},
            sink1__initial={'c': 5, 'd': 6},
            mode=datastructs.ReplicationMode.FULL,
        )
        for sink in sinks:
            self.assertEqual({}, sink.created)
            self.assertEqual({}, sink.updated)
            self.assertEqual(['c', 'd'], sorted(sink.deleted))

    def test_no_change(self):
        sinks = self._replicate(
            source__data={'a': 1, 'b': 2},
            sink0__initial={'a': 1, 'b': 2},
            sink1__initial={'a': 1, 'b': 2},
            mode=datastructs.ReplicationMode.FULL,
        )
        for sink in sinks:
            self.assertEqual({}, sink.created)
            self.assertEqual({}, sink.updated)
            self.assertEqual([], sink.deleted)

    def test_mixed(self):
        sinks = self._replicate(
            source__data={'a': 1, 'b': 2},
            sink0__initial={'b': 3, 'c': 4},
            sink1__initial={'a': 2, 'd': 5},
            mode=datastructs.ReplicationMode.FULL,
        )
        sink0, sink1 = sinks
        self.assertEqual({'a': 1}, sink0.created)
        self.assertEqual({'b': 2}, sink0.updated)
        self.assertEqual(['c'], sink0.deleted)

        self.assertEqual({'b': 2}, sink1.created)
        self.assertEqual({'a': 1}, sink1.updated)
        self.assertEqual(['d'], sink1.deleted)


    # Using the ThresholdDecider
    # ==========================

    def test_created_threshold_pass(self):
        sink0, sink1 = self._replicate(
            source__data={'a': 1, 'b': 2},
            sink0__initial={'a': 1},
            sink1__initial={'a': 1, 'b': 2},
            mode=datastructs.ReplicationMode.ADDITIVE,
            interactor__decider=factories.ThresholDeciderFactory(
                created_ratio=0.6,
            ),
        )
        self.assertEqual({'b': 2}, sink0.created)
        self.assertEqual({}, sink0.updated)
        self.assertEqual([], sink0.deleted)

        self.assertEqual({}, sink1.created)
        self.assertEqual({}, sink1.updated)
        self.assertEqual([], sink1.deleted)

    def test_created_threshold_break(self):
        sink0, sink1 = self._replicate(
            source__data={'a': 1, 'b': 2},
            sink0__initial={'a': 1},
            sink1__initial={'a': 1, 'b': 2},
            mode=datastructs.ReplicationMode.ADDITIVE,
            interactor__decider=factories.ThresholDeciderFactory(
                created_ratio=0.1,
            ),
        )
        self.assertEqual({}, sink0.created)
        self.assertEqual({}, sink0.updated)
        self.assertEqual([], sink0.deleted)

        self.assertEqual({}, sink1.created)
        self.assertEqual({}, sink1.updated)
        self.assertEqual([], sink1.deleted)

    def test_updated_threshold_pass(self):
        sink0, sink1 = self._replicate(
            source__data={'a': 1, 'b': 2},
            sink0__initial={'a': 1, 'b': 1},
            sink1__initial={'a': 1, 'b': 2},
            mode=datastructs.ReplicationMode.ADDITIVE,
            interactor__decider=factories.ThresholDeciderFactory(
                updated_ratio=0.6,
            ),
        )
        self.assertEqual({}, sink0.created)
        self.assertEqual({'b': 2}, sink0.updated)
        self.assertEqual([], sink0.deleted)

        self.assertEqual({}, sink1.created)
        self.assertEqual({}, sink1.updated)
        self.assertEqual([], sink1.deleted)

    def test_updated_threshold_break(self):
        sink0, sink1 = self._replicate(
            source__data={'a': 1, 'b': 2},
            sink0__initial={'a': 1, 'b': 1},
            sink1__initial={'a': 1, 'b': 2},
            mode=datastructs.ReplicationMode.ADDITIVE,
            interactor__decider=factories.ThresholDeciderFactory(
                updated_ratio=0.1,
            ),
        )
        self.assertEqual({}, sink0.created)
        self.assertEqual({}, sink0.updated)
        self.assertEqual([], sink0.deleted)

        self.assertEqual({}, sink1.created)
        self.assertEqual({}, sink1.updated)
        self.assertEqual([], sink1.deleted)

    def test_deleted_threshold_pass(self):
        sink0, sink1 = self._replicate(
            source__data={'a': 1, 'b': 2},
            sink0__initial={'a': 1, 'b': 2, 'c': 3},
            sink1__initial={'a': 1, 'b': 2},
            mode=datastructs.ReplicationMode.FULL,
            interactor__decider=factories.ThresholDeciderFactory(
                deleted_ratio=0.6,
            ),
        )
        self.assertEqual({}, sink0.created)
        self.assertEqual({}, sink0.updated)
        self.assertEqual(['c'], sink0.deleted)

        self.assertEqual({}, sink1.created)
        self.assertEqual({}, sink1.updated)
        self.assertEqual([], sink1.deleted)

    def test_deleted_threshold_break(self):
        sink0, sink1 = self._replicate(
            source__data={'a': 1, 'b': 2},
            sink0__initial={'a': 1, 'b': 2, 'c': 3},
            sink1__initial={'a': 1, 'b': 2},
            mode=datastructs.ReplicationMode.FULL,
            interactor__decider=factories.ThresholDeciderFactory(
                deleted_ratio=0.1,
            ),
        )
        self.assertEqual({}, sink0.created)
        self.assertEqual({}, sink0.updated)
        self.assertEqual([], sink0.deleted)

        self.assertEqual({}, sink1.created)
        self.assertEqual({}, sink1.updated)
        self.assertEqual([], sink1.deleted)

    # ShellDecider
    # ============

    def test_shell_keep(self):
        sink0, sink1 = self._replicate(
            source__data={'a': 1},
            sink0__initial={'a': 2},
            sink1__initial={'b': 2},
            mode=datastructs.ReplicationMode.FULL,
            interactor__decider=factories.ShellDeciderFactory(
                stdin=[''],
            ),
        )
        self.assertEqual({}, sink0.created)
        self.assertEqual({'a': 1}, sink0.updated)
        self.assertEqual([], sink0.deleted)

        self.assertEqual({'a': 1}, sink1.created)
        self.assertEqual({}, sink1.updated)
        self.assertEqual(['b'], sink1.deleted)

    def test_shell_fail_and_fix(self):
        sink0, sink1 = self._replicate(
            source__data={'a': 1},
            sink0__initial={'a': 2},
            sink1__initial={'b': 2},
            mode=datastructs.ReplicationMode.FULL,
            interactor__decider=factories.ShellDeciderFactory(
                stdin=['a', 'b', '42', ''],
            ),
        )
        self.assertEqual({}, sink0.created)
        self.assertEqual({'a': 1}, sink0.updated)
        self.assertEqual([], sink0.deleted)

        self.assertEqual({'a': 1}, sink1.created)
        self.assertEqual({}, sink1.updated)
        self.assertEqual(['b'], sink1.deleted)

    def test_shell_switch_full(self):
        sink0, sink1 = self._replicate(
            source__data={'a': 1},
            sink0__initial={'a': 2},
            sink1__initial={'b': 2},
            mode=datastructs.ReplicationMode.ADDITIVE,
            interactor__decider=factories.ShellDeciderFactory(
                stdin=['2'],
            ),
        )
        self.assertEqual({}, sink0.created)
        self.assertEqual({'a': 1}, sink0.updated)
        self.assertEqual([], sink0.deleted)

        self.assertEqual({'a': 1}, sink1.created)
        self.assertEqual({}, sink1.updated)
        self.assertEqual(['b'], sink1.deleted)

    def test_shell_switch_additive(self):
        sink0, sink1 = self._replicate(
            source__data={'a': 1},
            sink0__initial={'a': 2},
            sink1__initial={'b': 2},
            mode=datastructs.ReplicationMode.FULL,
            interactor__decider=factories.ShellDeciderFactory(
                stdin=['1'],
            ),
        )
        self.assertEqual({}, sink0.created)
        self.assertEqual({'a': 1}, sink0.updated)
        self.assertEqual([], sink0.deleted)

        self.assertEqual({'a': 1}, sink1.created)
        self.assertEqual({}, sink1.updated)
        self.assertEqual([], sink1.deleted)

    def test_shell_switch_dryrun(self):
        sink0, sink1 = self._replicate(
            source__data={'a': 1},
            sink0__initial={'a': 2},
            sink1__initial={'b': 2},
            mode=datastructs.ReplicationMode.FULL,
            interactor__decider=factories.ShellDeciderFactory(
                stdin=['0'],
            ),
        )
        self.assertEqual({}, sink0.created)
        self.assertEqual({}, sink0.updated)
        self.assertEqual([], sink0.deleted)

        self.assertEqual({}, sink1.created)
        self.assertEqual({}, sink1.updated)
        self.assertEqual([], sink1.deleted)
