# Docker Plugin for PAKA

The Docker plugin allows PAKA to treat Docker containers as packages, providing a unified interface for managing Docker containers alongside traditional packages.

## Features

- **Container Search**: Search Docker Hub for available containers
- **Container Installation**: Pull and install Docker containers
- **Container Removal**: Remove Docker container images
- **Container Updates**: Update containers to latest versions
- **Installed Tracking**: Track which containers are installed
- **Multi-Registry Support**: Support for Docker Hub, Quay.io, and other registries

## Usage

### Search for Containers
```bash
paka search nginx --manager docker
```

### Install a Container
```bash
paka install nginx --manager docker
```

### Remove a Container
```bash
paka remove nginx --manager docker
```

### Update Containers
```bash
paka upgrade --manager docker
```

## Configuration

The plugin supports the following configuration options:

- `registries`: List of Docker registries to search (default: ["docker.io", "quay.io"])
- `enabled`: Whether the plugin is enabled (default: false)

## Requirements

- Docker must be installed and running on the system
- User must have permission to run Docker commands

## Examples

### Search for Web Servers
```bash
paka search "web server" --manager docker
```

### Install Multiple Containers
```bash
paka install nginx postgres redis --manager docker
```

### Check for Updates
```bash
paka upgrade --manager docker
```

## Integration

The Docker plugin integrates seamlessly with PAKA's unified interface:

- Search results show container information including stars, official status, and automation
- Installation tracks containers in PAKA's history system
- Health checks can verify Docker service status
- Plugin events trigger appropriate actions during container operations

## Troubleshooting

### Docker Not Available
If Docker is not installed or not running, the plugin will be disabled automatically.

### Permission Issues
Ensure your user is in the `docker` group or has appropriate permissions to run Docker commands.

### Network Issues
If you're behind a proxy or firewall, configure Docker accordingly for registry access. 