# Copyright 2024 Ubuntu
# See LICENSE file for licensing details.

"""Implementation of cert-manager kubernetes manifests."""

import logging
import pickle
from hashlib import md5
from typing import Dict

from ops.manifests import ManifestLabel, Manifests

log = logging.getLogger()


class CertManagerManifests(Manifests):
    """Deployment details for cert-manager."""

    def __init__(self, charm, charm_config):
        super().__init__(
            "cert-manager",
            charm.model,
            "upstream/cert-manager",
            [
                ManifestLabel(self),
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

        config["release"] = config.pop("cert-manager-release", None)

        return config

    def hash(self) -> int:
        """Calculate a hash of the current configuration."""
        return int(md5(pickle.dumps(self.config)).hexdigest(), 16)
