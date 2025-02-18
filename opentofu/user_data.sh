#!/bin/sh
# When running this via Terraform user data, this will run via /bin/sh and that is out of our control, even if you change the above shebang
# Also, set -o pipefail is not supported in POSIX SH
set -eu

export DEBIAN_FRONTEND=noninteractive
export USER
USER="$(id -nu 1000)"
export USER_HOME="/home/${USER}"
echo "export PATH=\${HOME}/.local/bin:\${PATH}" >> "${USER_HOME}/.bashrc"

## Install uv, python, some standard packages
# uv's install script expects HOME to be set
cd "${USER_HOME}" # in POSIX sh, pushd is undefined
curl -LsSf https://astral.sh/uv/install.sh | HOME="${USER_HOME}" UV_INSTALL_DIR="${USER_HOME}/.local/bin" sh
chown -R "${USER}":"${USER}" "${USER_HOME}"
export PATH="${USER_HOME}/.local/bin:${PATH}"
sudo --preserve-env=USER_HOME \
    -u "${USER}" /bin/bash -c '
        export PATH="${USER_HOME}/.local/bin:${PATH}" &&
        uv python install &&
        uv venv &&
        uv pip install psycopg
        '

## Install some baseline tools
# In the future we want to move from python3-pip to uv pip
sudo apt-get update
sudo apt -y install nmap \
                    net-tools \
                    postgresql-client \
                    unzip \
                    python3-pip

## Install the aws cli
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip

## Install and setup docker
apt-get -y install apt-transport-https \
                   ca-certificates \
                   curl \
                   gnupg \
                   lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get -y install docker-ce \
                   docker-ce-cli \
                   containerd.io
sudo usermod -aG docker "${USER}"

## Makes sure the user owns the files in their home directory
chown -R "${USER}":"${USER}" "${USER_HOME}"

# This triggers follow-on work to continue
echo "Setup complete" > /tmp/user_data_done
