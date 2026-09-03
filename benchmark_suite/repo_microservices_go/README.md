# 🛒 Distributed Microservices Backend (Go)

Enterprise-grade event-driven microservices architecture built with Go, gRPC, Redis, and PostgreSQL.

## Architecture
- **Auth Service**: Issues and validates JWT identity claims.
- **Order Service**: Coordinates order placement, inventory reservations, and payment processing.
- **Event Bus**: Redis Pub/Sub for asynchronous state synchronization.

## Installation
```bash
docker-compose up -d
go test ./...
```

## Environment Variables
- `JWT_SECRET`: Secret key used for signing auth tokens.
- `DATABASE_URL`: PostgreSQL connection string.
- `REDIS_URL`: Redis host endpoint.

## License
MIT
