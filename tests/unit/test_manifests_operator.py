# Copyright 2024 Ubuntu
# See LICENSE file for licensing details.

import unittest.mock as mock

import pytest
from charm import IntelDevicePluginsK8SOperatorCharm
from manifests_operator import PatchPluginName
from ops.testing import Harness


@pytest.fixture
def harness():
    harness = Harness(IntelDevicePluginsK8SOperatorCharm)
    try:
        harness.begin()
        harness.set_leader(is_leader=True)
        yield harness
    finally:
        harness.cleanup()


def test_patch_plugin_name(harness: Harness):
    patch = PatchPluginName(harness.charm.collector.manifests)
    obj = mock.MagicMock()
    d = {"kind": "GpuDevicePlugin", "metadata": {"name": "mockdeviceplugin-sample"}}
    obj.__getitem__.side_effect = d.__getitem__
    obj.kind = d["kind"]
    patch(obj)
    assert obj["metadata"]["name"] == "mockdeviceplugin"
