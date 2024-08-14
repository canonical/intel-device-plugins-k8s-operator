#!/bin/bash
#
# Provision device for charms with microk8s
#
# Note, much of this is borrowed from the
# charm-dev multipass template:
# https://github.com/canonical/multipass-blueprints/blob/main/v1/charm-dev.yaml

# Install apt and snap packages here instead
# of in "packages" and "snap" sections
# to ensure everything runs sequentially
DEBIAN_FRONTEND=noninteractive apt update
DEBIAN_FRONTEND=noninteractive apt -y upgrade
DEBIAN_FRONTEND=noninteractive apt -y install python3-pip

# Juju 3.5 is supported until Jan 2025
# https://juju.is/docs/juju/roadmap
snap install juju --channel=3.5/stable
snap install microk8s --channel=1.30-strict/stable
snap install --classic charmcraft --channel=3.x/stable
snap install lxd --channel=5.21/stable
snap refresh

# Install tox from pypi (v4) instead of apt (v3)
pip install tox

# Disable swap
sysctl -w vm.swappiness=0
echo "vm.swappiness = 0" | tee -a /etc/sysctl.conf
swapoff -a

# Disable IPv6
echo "net.ipv6.conf.all.disable_ipv6=1" | tee -a /etc/sysctl.conf
echo "net.ipv6.conf.default.disable_ipv6=1" | tee -a /etc/sysctl.conf
echo "net.ipv6.conf.lo.disable_ipv6=1" | tee -a /etc/sysctl.conf
sysctl -p

# Make sure juju directory is present
# https://bugs.launchpad.net/juju/+bug/1995697
sudo -u ubuntu mkdir -p /home/ubuntu/.local/share/juju

# setup lxd for charmcraft
lxd init --auto
adduser ubuntu lxd

# setup microk8s
usermod -a -G snap_microk8s ubuntu
usermod -a -G microk8s ubuntu
microk8s status --wait-ready
microk8s.enable dns
microk8s.kubectl rollout status \
  deployments/coredns \
  -n kube-system -w --timeout=1800s
# Give microk8s another minute to stabilize
# to avoid intermittent failures when
# enabling hostpath-storage
sleep 60
microk8s.enable hostpath-storage
  microk8s.kubectl rollout status \
  deployments/hostpath-provisioner \
  -n kube-system -w --timeout=1800s

# bootstrap microk8s controller and add model
sudo -u ubuntu juju bootstrap microk8s microk8s
sudo -u ubuntu juju add-model \
  --config logging-config="<root>=WARNING; unit=DEBUG" \
  --config update-status-hook-interval="1m" \
  welcome-k8s