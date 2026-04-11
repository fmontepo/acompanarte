-- docker/init.sql
-- Este script se ejecuta automáticamente cuando PostgreSQL crea la DB por primera vez
-- Activa la extensión pgvector necesaria para los embeddings RAG

CREATE EXTENSION IF NOT EXISTS vector;
