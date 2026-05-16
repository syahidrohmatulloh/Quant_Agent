
# Deployment Guide

## Paper Trading Only

This system is configured for **paper trading only** by default.
Do not enable live trading without explicit safety review.

## Docker

```bash
cd deployment
docker-compose up --build
```

## Environment

Copy `.env.example` to `.env` and configure tokens.

## Health Check

```bash
curl http://localhost:8000/health
```

## PostgreSQL (Optional)

Uncomment the postgres service in `docker-compose.yml` and run:
```bash
docker-compose --profile postgres up
```
