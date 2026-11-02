#!/bin/bash
set -e
echo "=== Deploy SPM JPN Selangor to Hostinger KVM ==="
apt update -y
apt install -y docker.io docker-compose unzip
systemctl enable --now docker

# create swap 2GB for 4GB KVM (optimize)
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

cd /opt
mkdir -p spm && cd spm
echo "Upload SPM_FINAL_VPS_RM30_ALL_OK.zip ke /opt/spm dan unzip..."
# if zip already there, unzip
if ls *.zip 1> /dev/null 2>&1; then
  unzip -o *.zip
fi

# ensure requirements
pip3 install -r requirements.txt || pip install -r requirements.txt

# build & run
docker-compose down || true
docker-compose up -d --build
echo "=== DONE ==="
echo "SPM jalan di http://187.53.128.19:8501"
docker logs -f spm_jpn --tail 50
