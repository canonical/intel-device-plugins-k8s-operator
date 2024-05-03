# Copyright 2024 Ubuntu
# See LICENSE file for licensing details.

"""Implementation of intel-device-plugins-operator kubernetes manifests."""

import logging
import pickle
from hashlib import md5
from typing import Dict

from ops.manifests import ConfigRegistry, ManifestLabel, Manifests, Patch

log = logging.getLogger()


class RemoveNamespace(Patch):
    """Remove namespace from resources so they deploy to the charm's namespace."""

    def __call__(self, obj):
        """Remove namespace from resources."""
        obj.metadata.namespace = None


class IntelDevicePluginsK8SOperatorManifests(Manifests):
    """Deployment details for intel-device-plugins-k8s-operator."""

    def __init__(self, charm, charm_config):
        super().__init__(
            "intel-device-plugins-operator",
            charm.model,
            "upstream/intel-device-plugins-operator",
            [
                ManifestLabel(self),
                ConfigRegistry(self),
                # RemoveNamespace(self),
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
