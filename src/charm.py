#!/usr/bin/env python3
# Copyright 2024 Ubuntu
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Dispatch logic for the intel-device-plugins-k8s charm."""

import logging

from manifests_cert_manager import CertManagerManifests
from manifests_operator import IntelDevicePluginsK8SOperatorManifests
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.manifests import Collector, ManifestClientError
from ops.model import ActiveStatus, MaintenanceStatus, WaitingStatus

# Log messages can be retrieved using juju debug-log
log = logging.getLogger()


class IntelDevicePluginsK8sCharm(CharmBase):
    """Charm the service."""

    stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        self.stored.set_default(
            config_hash=None,  # hashed value of the applied config once valid
            deployed=False,  # True if the config has been applied after new hash
        )
        self.collector = Collector(
            CertManagerManifests(self, self.config),
            IntelDevicePluginsK8SOperatorManifests(self, self.config),
        )

        self.framework.observe(self.on.update_status, self._update_status)
        self.framework.observe(self.on.install, self._install_or_upgrade)
        self.framework.observe(self.on.upgrade_charm, self._install_or_upgrade)
        self.framework.observe(self.on.config_changed, self._merge_config)
        self.framework.observe(self.on.stop, self._cleanup)
        self.framework.observe(self.on.list_versions_action, self._list_versions)
        self.framework.observe(self.on.list_resources_action, self._list_resources)
        self.framework.observe(self.on.scrub_resources_action, self._scrub_resources)
        self.framework.observe(self.on.sync_resources_action, self._sync_resources)

    def _list_versions(self, event):
        self.collector.list_versions(event)

    def _list_resources(self, event):
        manifests = event.params.get("controller", "")
        resources = event.params.get("resources", "")
        return self.collector.list_resources(event, manifests, resources)

    def _scrub_resources(self, event):
        manifests = event.params.get("controller", "")
        resources = event.params.get("resources", "")
        return self.collector.scrub_resources(event, manifests, resources)

    def _sync_resources(self, event):
        manifests = event.params.get("controller", "")
        resources = event.params.get("resources", "")
        try:
            self.collector.apply_missing_resources(event, manifests, resources)
        except ManifestClientError:
            msg = "Failed to apply missing resources. API Server unavailable."
            event.set_results({"result": msg})
        else:
            self.stored.deployed = True

    def _update_status(self, _):
        if not self.stored.deployed:
            return

        unready = self.collector.unready
        if unready:
            self.unit.status = WaitingStatus(", ".join(unready))
        else:
            self.unit.status = ActiveStatus("Ready")
            self.unit.set_workload_version(self.collector.short_version)
            self.app.status = ActiveStatus(self.collector.long_version)

    def _merge_config(self, event):
        self.unit.status = MaintenanceStatus("Evaluating Manifests")
        new_hash = 0
        for controller in self.collector.manifests.values():
            new_hash += controller.hash()

        self.stored.deployed = False
        if self._install_or_upgrade(event, config_hash=new_hash):
            self.stored.config_hash = new_hash
            self.stored.deployed = True

    def _install_or_upgrade(self, event, config_hash=None):
        if self.stored.config_hash == config_hash:
            log.info("Skipping until the config is evaluated.")
            return True

        self.unit.status = MaintenanceStatus("Deploying Intel Device Plugins Operator")
        self.unit.set_workload_version("")
        for controller in self.collector.manifests.values():
            try:
                controller.apply_manifests()
            except ManifestClientError as e:
                self.unit.status = WaitingStatus("Waiting for kube-apiserver")
                log.warning(f"Encountered retryable installation error: {e}")
                event.defer()
                return False
        return True

    def _cleanup(self, event):
        if self.stored.config_hash:
            self.unit.status = MaintenanceStatus("Cleaning up Intel Device Plugins Operator")
            for controller in self.collector.manifests.values():
                try:
                    controller.delete_manifests(ignore_unauthorized=True)
                except ManifestClientError:
                    self.unit.status = WaitingStatus("Waiting for kube-apiserver")
                    event.defer()
                    return
        self.unit.status = MaintenanceStatus("Shutting down")


if __name__ == "__main__":  # pragma: nocover
    main(IntelDevicePluginsK8sCharm)  # type: ignore
