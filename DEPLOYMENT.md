# Deployment Guide

This document provides instructions for deploying the AI Resume Analyzer to a production VPS using Docker Compose and Caddy.

## Prerequisites

- A VPS (Ubuntu 22.04+ recommended)
- Docker and Docker Compose installed
- A domain name with A records pointing to your VPS IP

## Setup Steps

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/AI-resume-analyzer.git
    cd AI-resume-analyzer
    ```

2.  **Configure Environment**:
    ```bash
    cp .env.prod.example .env.prod
    # Edit .env.prod with your production values
    nano .env.prod
    ```

3.  **Start with Production Overlay**:
    ```bash
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d
    ```

4.  **Run Migrations**:
    ```bash
    docker-compose exec api alembic upgrade head
    ```

## HTTPS and Reverse Proxy

If you are using Caddy (recommended):
1. Install Caddy on your host or add a Caddy service to your compose file.
2. Use the provided `Caddyfile` template.

## Backups

### Database Dump
Create a cron job to backup your database:
```bash
0 2 * * * docker exec -t $(docker ps -qf "name=_db_") pg_dumpall -c -U resume_prod_user > /path/to/backups/dump_$(date +\%F).sql
```

## Maintenance

- **Logs**: `docker-compose logs -f`
- **Update**: `git pull && docker-compose build && docker-compose up -d`
