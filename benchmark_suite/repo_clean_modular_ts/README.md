# Clean Modular TypeScript Application

A production-grade TypeScript fullstack microservice with clean architecture, strict typing, and comprehensive test suites.

## Installation

```bash
npm install
npm run build
```

## Usage

```bash
npm run dev
```

## Architecture

This repository uses a modular multi-tier architecture:
- `src/controllers`: Request handlers and route mapping
- `src/services`: Pure business logic
- `src/repositories`: Database access layer via parameterized queries
- `src/config`: Environment variable schema validation via Zod

## Environment Configuration

Configure the following variables in `.env`:
- `DATABASE_URL`: Connection string for PostgreSQL
- `PORT`: Server port (default 3000)

## License

MIT
