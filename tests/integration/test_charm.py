#!/usr/bin/env python3
# Copyright 2024 Ubuntu
# See LICENSE file for licensing details.

import asyncio
import logging
from pathlib import Path

import pytest
import yaml
from lightkube import AsyncClient
from lightkube.resources.core_v1 import Node
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(Path("./charmcraft.yaml").read_text())
APP_NAME = METADATA["name"]


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest):
    """Build the charm-under-test and deploy it together with related charms.

    Assert on the unit status before any relations/configurations take place.
    """
    # Build and deploy charm from local source folder
    charm = await ops_test.build_charm(".")

    # Deploy the charm and wait for active/idle status
    await asyncio.gather(
        ops_test.model.deploy(charm, application_name=APP_NAME, trust=True),
        ops_test.model.wait_for_idle(
            apps=[APP_NAME], status="active", raise_on_blocked=True, timeout=1800
        ),
    )


async def test_charm_status(ops_test: OpsTest):
    application = ops_test.model.applications[APP_NAME]
    units = application.units
    cert_manager_latest_version = Path("upstream", "cert-manager", "version").read_text().strip()
    operator_latest_version = (
        Path("upstream", "intel-device-plugins-operator", "version").read_text().strip()
    )
    assert units[0].workload_status == "active"
    assert units[0].workload_status_message == "Ready"
    assert application.status == "active"
    assert (
        application.workload_version == f"{cert_manager_latest_version},{operator_latest_version}"
    )


async def test_node_label(kubernetes: AsyncClient):
    """Verify that expected node label is present.

    This will fail if an Intel GPU is not present on the system.
    """
    async for node in kubernetes.list(Node):
        assert node.metadata.labels["intel.feature.node.kubernetes.io/gpu"] == "true"


async def test_node_status(kubernetes: AsyncClient):
    """Verify that the number of GPU slots are the expected value."""
    async for node in kubernetes.list(Node):
        # The plugin is configured to allow up to 10 containers
        # access to each GPU
        slots_per_gpu = 10
        gpu_count = sum(
            [
                int(val)
                for key, val in node.metadata.labels.items()
                if key.startswith("gpu.intel.com/device-id.") and key.endswith(".count")
            ]
        )
        slots = gpu_count * slots_per_gpu
        assert node.status.capacity["gpu.intel.com/i915"] == str(slots)
        assert node.status.allocatable["gpu.intel.com/i915"] == str(slots)


async def test_adjust_version(ops_test: OpsTest):
    """Verify that the application versions can be adjusted."""
    update_status_timeout = 1800
    application = ops_test.model.applications[APP_NAME]
    await application.set_config({"intel-device-plugins-operator-release": "0.29.0"})
    await ops_test.model.wait_for_idle(status="active", timeout=update_status_timeout)
    await application.reset_config(["intel-device-plugins-operator-release"])
    await ops_test.model.wait_for_idle(status="active", timeout=update_status_timeout)
    await application.set_config({"cert-manager-release": "v1.14.5"})
    await ops_test.model.wait_for_idle(status="active", timeout=update_status_timeout)
    await application.reset_config(["cert-manager-release"])
    await ops_test.model.wait_for_idle(status="active", timeout=update_status_timeout)
