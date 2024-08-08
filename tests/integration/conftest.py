# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import pytest_asyncio
from lightkube import AsyncClient, KubeConfig


@pytest_asyncio.fixture(scope="module")
async def kubernetes(request):
    config = KubeConfig.from_file("/var/snap/microk8s/current/credentials/client.config")
    client = AsyncClient(config=config)
    yield client
