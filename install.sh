#!/bin/bash

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VERSION=$VERSION_ID
else
    echo "Cannot detect OS, exiting..."
    exit 1
fi

# Define credentials
MONGO_USERNAME="admin"
MONGO_PASSWORD="SmartHirink@2024"
RABBITMQ_USERNAME="admin"
RABBITMQ_PASSWORD="SmartHirink@2024"

# Update package list
case $OS in
    "Ubuntu")
        PKG_MANAGER="apt-get"
        DOCKER_REPO_URL="https://download.docker.com/linux/ubuntu"
        ;;
    "Debian GNU/Linux")
        PKG_MANAGER="apt-get"
        DOCKER_REPO_URL="https://download.docker.com/linux/debian"
        ;;
    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac

sudo $PKG_MANAGER update

# Install poppler-utils
sudo $PKG_MANAGER install -y poppler-utils

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 not found, installing..."
    sudo $PKG_MANAGER install -y python3 python3-pip
else
    echo "Python3 is already installed"
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null
then
    echo "Poetry not found, installing..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "Poetry is already installed"
fi

# Add poetry-dotenv-plugin
poetry self add poetry-dotenv-plugin

# Install project dependencies
poetry install

# Check if Docker is installed
if ! command -v docker &> /dev/null
then
    echo "Docker not found, installing..."
    # Install dependencies
    sudo $PKG_MANAGER install -y apt-transport-https ca-certificates curl gnupg

    # Add Docker's official GPG key
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL $DOCKER_REPO_URL/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    # Add Docker repository based on OS
    echo \
      "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] $DOCKER_REPO_URL \
      "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Update package list and install Docker
    sudo $PKG_MANAGER update
    sudo $PKG_MANAGER install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
    echo "Docker is already installed"
fi

# Pull and run MongoDB and Redis containers if not already running
if [ ! "$(sudo docker ps -q -f name=mongodb)" ]; then
    if [ "$(sudo docker ps -aq -f status=exited -f name=mongodb)" ]; then
        # Cleanup
        sudo docker rm mongodb
    fi
    sudo docker run -d --name mongodb \
        -p 27017:27017 \
        -e MONGO_INITDB_ROOT_USERNAME=$MONGO_USERNAME \
        -e MONGO_INITDB_ROOT_PASSWORD=$MONGO_PASSWORD \
        mongo
else
    echo "MongoDB container is already running"
fi

if [ ! "$(sudo docker ps -q -f name=redis)" ]; then
    if [ "$(sudo docker ps -aq -f status=exited -f name=redis)" ]; then
        # Cleanup
        sudo docker rm redis
    fi
    sudo docker run -d --name redis -p 6379:6379 redis
else
    echo "Redis container is already running"
fi

# Pull and run RabbitMQ container if not already running
if [ ! "$(sudo docker ps -q -f name=rabbitmq)" ]; then
    if [ "$(sudo docker ps -aq -f status=exited -f name=rabbitmq)" ]; then
        # Cleanup
        sudo docker rm rabbitmq
    fi
    sudo docker run -d --name rabbitmq \
        -p 5672:5672 -p 15672:15672 \
        -e RABBITMQ_DEFAULT_USER=$RABBITMQ_USERNAME \
        -e RABBITMQ_DEFAULT_PASS=$RABBITMQ_PASSWORD \
        rabbitmq:3-management
else
    echo "RabbitMQ container is already running"
fi

echo "Installation complete"