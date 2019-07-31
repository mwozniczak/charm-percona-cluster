import mock
from mock import patch

from test_utils import CharmTestCase

# we have to patch out harden decorator because hooks/percona_hooks.py gets
# imported via actions.py and will freak out if it trys to run in the context
# of a test.
with patch('charmhelpers.contrib.hardening.harden.harden') as mock_dec:
    mock_dec.side_effect = (lambda *dargs, **dkwargs: lambda f:
                            lambda *args, **kwargs: f(*args, **kwargs))
    from actions import actions


class PauseTestCase(CharmTestCase):

    def setUp(self):
        super(PauseTestCase, self).setUp(
            actions.percona_utils, ["pause_unit_helper", "register_configs"])

    def test_pauses_services(self):
        self.register_configs.return_value = "test-config"
        actions.pause([])
        self.pause_unit_helper.assert_called_once_with('test-config')


class ResumeTestCase(CharmTestCase):

    def setUp(self):
        super(ResumeTestCase, self).setUp(
            actions.percona_utils, ["resume_unit_helper", "register_configs"])

    def test_pauses_services(self):
        self.register_configs.return_value = "test-config"
        with patch('actions.actions.percona_hooks.config_changed'
                   ) as config_changed:
            actions.resume([])
            self.resume_unit_helper.assert_called_once_with('test-config')
            config_changed.assert_called_once_with()


class CompleteClusterSeriesUpgrade(CharmTestCase):

    def setUp(self):
        super(CompleteClusterSeriesUpgrade, self).setUp(
            actions, ["is_leader", "leader_set"])

    def test_leader_complete_series_upgrade(self):
        self.is_leader.return_value = True
        calls = [mock.call(cluster_series_upgrading=""),
                 mock.call(cluster_series_upgrade_leader="")]
        with patch('actions.actions.percona_hooks.config_changed'
                   ) as config_changed:
            actions.complete_cluster_series_upgrade([])
            self.leader_set.assert_has_calls(calls)
            config_changed.assert_called_once_with()

    def test_non_leader_complete_series_upgrade(self):
        self.is_leader.return_value = False
        with patch('actions.actions.percona_hooks.config_changed'
                   ) as config_changed:
            actions.complete_cluster_series_upgrade([])
            self.leader_set.assert_not_called()
            config_changed.assert_called_once_with()


class MainTestCase(CharmTestCase):

    def setUp(self):
        super(MainTestCase, self).setUp(actions, ["action_fail"])

    def test_invokes_action(self):
        dummy_calls = []

        def dummy_action(args):
            dummy_calls.append(True)

        with mock.patch.dict(actions.ACTIONS, {"foo": dummy_action}):
            actions.main(["foo"])
        self.assertEqual(dummy_calls, [True])

    def test_unknown_action(self):
        """Unknown actions aren't a traceback."""
        exit_string = actions.main(["foo"])
        self.assertEqual("Action foo undefined", exit_string)

    def test_failing_action(self):
        """Actions which traceback trigger action_fail() calls."""
        dummy_calls = []

        self.action_fail.side_effect = dummy_calls.append

        def dummy_action(args):
            raise ValueError("uh oh")

        with mock.patch.dict(actions.ACTIONS, {"foo": dummy_action}):
            actions.main(["foo"])
        self.assertEqual(dummy_calls, ["Action foo failed: uh oh"])
