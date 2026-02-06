# StudentVC Deployment

This directory contains all deployment-related files and scripts for the StudentVC multi-tenant verifiable credential platform.

## Directory Structure

```
deploy/
├── scripts/              # Deployment scripts
│   ├── deploy.sh         # Main deployment orchestrator
│   ├── deploy-docker-all.sh    # Deploy all tenants
│   ├── deploy-docker-tub.sh    # Deploy TU Berlin tenant only
│   ├── deploy-docker-fub.sh    # Deploy FU Berlin tenant only
│   ├── deploy-docker-root.sh   # Deploy Root tenant only
│   └── deploy-kubernetes.sh    # Kubernetes deployment
├── configs/              # Configuration files
│   ├── docker-compose.yml      # Multi-tenant Docker Compose
│   ├── docker-compose-restricted.yml  # With colleague access
│   ├── nginx.conf       # NGINX reverse proxy config
│   ├── kubernetes/      # Kubernetes manifests
│   ├── ssl/            # SSL certificates
│   ├── static/         # Static assets per tenant
│   └── data/           # Database files per tenant
└── README.md           # This file
```

## Quick Start

### From Root Directory (Recommended)

```bash
# Multi-tenant deployment (all tenants)
./deploy.sh

# Single tenant deployment
SINGLE_TENANT=tub ./deploy.sh    # TU Berlin only
SINGLE_TENANT=fub ./deploy.sh    # FU Berlin only
SINGLE_TENANT=root ./deploy.sh   # Root only

# Kubernetes deployment
./deploy.sh kubernetes
```

### Direct Script Execution

```bash
# From deploy/scripts/ directory
cd deploy/scripts

# Deploy all tenants
./deploy-docker-all.sh

# Deploy individual tenants
./deploy-docker-tub.sh
./deploy-docker-fub.sh
./deploy-docker-root.sh

# Kubernetes deployment
./deploy-kubernetes.sh
```

## Tenant Isolation

Each tenant operates with complete isolation:

- **Separate databases**: `configs/data/{tenant}/`
- **Custom branding**: `configs/static/{tenant}/`
- **Unique cryptographic keys**: Generated per tenant
- **Independent configuration**: `configs/` per tenant

## Access URLs

After deployment:

- **TU Berlin**: https://localhost:8080
- **FU Berlin**: https://localhost:8081
- **Root/Default**: https://localhost:8082

## Environment Configuration

Copy `deployment.env` to `.env` and configure:

```bash
cp deployment.env .env
nano .env  # Edit your settings
```

Key settings:
- NGROK URLs for mobile wallet access
- Secret keys (change in production!)
- SSL configuration
- Resource limits

## Monitoring

```bash
# View all logs
docker compose -f configs/docker-compose.yml logs -f

# View specific tenant
docker logs studentvc-tub -f

# Check status
docker ps
```

## Production Considerations

1. **Security**: Change all default passwords and secret keys
2. **SSL**: Add proper certificates in `configs/ssl/`
3. **Backup**: Regular backup of `configs/data/` directories
4. **Monitoring**: Use Docker health checks and external monitoring
5. **Updates**: Use `docker compose up -d --build` for updates

## Professional Structure Benefits

- **Clean separation**: Scripts vs configurations
- **Easy maintenance**: All deployment files in one place
- **Version control**: Proper .gitignore for generated files
- **Scalability**: Easy to add new tenants or deployment methods
- **Documentation**: Each directory has clear purpose

For detailed deployment instructions, see the main [DEPLOYMENT.md](../DEPLOYMENT.md) file. 