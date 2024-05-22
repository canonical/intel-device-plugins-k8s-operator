# Copyright 2024 Ubuntu
# See LICENSE file for licensing details.

import unittest.mock as mock

import pytest
from charm import IntelDevicePluginsK8SOperatorCharm
from ops.model import ActiveStatus, MaintenanceStatus, WaitingStatus
from ops.testing import Harness


@pytest.fixture
def harness():
    harness = Harness(IntelDevicePluginsK8SOperatorCharm)
    try:
        harness.set_leader(is_leader=True)
        yield harness
    finally:
        harness.cleanup()


def test_update_status_ready(harness: Harness, lk_client):
    harness.begin_with_initial_hooks()
    harness.charm.on.update_status.emit()
    assert harness.charm.unit.status == ActiveStatus("Ready")


@mock.patch("charm.Collector.unready", new=["foobar is not ready"])
def test_update_status_waiting(harness: Harness, lk_client):
    harness.begin_with_initial_hooks()
    harness.charm.on.update_status.emit()
    assert harness.charm.unit.status == WaitingStatus("foobar is not ready")


def test_merge_config_success(harness: Harness, lk_client):
    harness.begin()
    harness.charm.on.config_changed.emit()
    assert harness.charm.unit.status == MaintenanceStatus(
        "Deploying Intel Device Plugins Operator"
    )


def test_merge_config_error(harness: Harness, lk_client, api_error_klass):
    lk_client.apply.side_effect = api_error_klass
    harness.begin()
    harness.charm.on.config_changed.emit()
    assert harness.charm.unit.status == WaitingStatus("Waiting for kube-apiserver")
