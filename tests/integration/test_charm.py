#!/usr/bin/env python3
# Copyright 2024 Ubuntu
# See LICENSE file for licensing details.

import asyncio
import logging
from pathlib import Path

import pytest
import yaml
from pytest_operator.plugin import OpsTest
from lightkube import Client
from lightkube.resources.core_v1 import Node

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

async def test_node_label(kubernetes: Client):
    """Verify that expected node label is present.

    This will fail if an Intel GPU is not present on the system.
    """
    async for node in kubernetes.list(Node):
        assert node.metadata.labels["intel.feature.node.kubernetes.io/gpu"] == "true"

async def test_node_status(kubernetes: Client):
    """Verify that the number of GPU slots are the expected value."""
    async for node in kubernetes.list(Node):
        assert node.status.capacity["gpu.intel.com/i915"] == "10"
        assert node.status.allocatable["gpu.intel.com/i915"] == "10"