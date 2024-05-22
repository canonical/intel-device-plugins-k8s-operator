# Copyright 2024 Ubuntu
# See LICENSE file for licensing details.

"""Implementation of intel-device-plugins-operator kubernetes manifests."""

import logging
import pickle
from hashlib import md5
from typing import Dict

from lightkube.codecs import AnyResource
from ops.manifests import ManifestLabel, Manifests, Patch

log = logging.getLogger()


class PatchPluginName(Patch):
    """Adjust name of device plugin from sample naming provided by Intel."""

    def __call__(self, obj: AnyResource) -> None:
        """Replace sample naming provided by Intel."""
        if obj.kind == "GpuDevicePlugin":
            upstream_name: str = obj["metadata"]["name"]
            if upstream_name.endswith("-sample"):
                log.info(f"Patching name for {obj.kind} {upstream_name}")
                obj["metadata"]["name"] = upstream_name.removesuffix("-sample")


class IntelDevicePluginsK8SOperatorManifests(Manifests):
    """Deployment details for intel-device-plugins-k8s-operator."""

    def __init__(self, charm, charm_config):
        super().__init__(
            "intel-device-plugins-operator",
            charm.model,
            "upstream/intel-device-plugins-operator",
            [
                ManifestLabel(self),
                PatchPluginName(self),
            ],
        )
        self.charm_config = charm_config

    @property
    def config(self) -> Dict:
        """Returns config mapped from charm config and joined relations."""
        config = dict(**self.charm_config)

        for key, value in dict(**config).items():
            if value == "" or value is None:
                del config[key]  # blank out keys not currently set to something

        return config

    def hash(self) -> int:
        """Calculate a hash of the current configuration."""
        return int(md5(pickle.dumps(self.config)).hexdigest(), 16)
