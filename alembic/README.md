# Alembic Migrations

This directory contains database migration scripts managed by Alembic.

## Why Alembic?

Using `Base.metadata.create_all()` in production is dangerous because:
- It doesn't handle schema changes (adding columns, indexes, etc.)
- It can't rollback changes
- It doesn't track migration history
- It can cause data loss if not careful

Alembic provides:
- Version control for database schema
- Safe migrations with rollback support
- Migration history tracking
- Automatic migration generation from model changes

## Setup

1. **Install Alembic** (if not already installed):
```bash
pip install alembic
```

2. **Configure database URL** in `.env`:
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
```

## Common Commands

### Create a new migration
```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration (for manual changes)
alembic revision -m "description"
```

### Apply migrations
```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision_id>

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

### Check migration status
```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

## Migration Workflow

1. **Modify models** in `app/infrastructure/persistence/models_relational.py`

2. **Generate migration**:
```bash
alembic revision --autogenerate -m "add new column to messages"
```

3. **Review generated migration** in `alembic/versions/`

4. **Apply migration**:
```bash
alembic upgrade head
```

5. **Test rollback** (optional):
```bash
alembic downgrade -1
alembic upgrade head
```

## Production Deployment

In production, migrations should be run as part of deployment:

```bash
# Before starting the application
alembic upgrade head
```

## Important Notes

- **Never edit existing migrations** - create new ones instead
- **Always test migrations** on a copy of production data first
- **Backup database** before running migrations in production
- **Review auto-generated migrations** - Alembic can't detect everything

## First Migration

To create the initial migration for existing models:

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

