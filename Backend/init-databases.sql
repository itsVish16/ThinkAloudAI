-- Auto-executed on first postgres container startup.
-- Creates one isolated database per microservice idempotently.

SELECT 'CREATE DATABASE user_service' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'user_service')\gexec
SELECT 'CREATE DATABASE main_service' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'main_service')\gexec
SELECT 'CREATE DATABASE interviewer_service' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'interviewer_service')\gexec
