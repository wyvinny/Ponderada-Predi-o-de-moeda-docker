CREATE TABLE retraining_jobs (id UUID PRIMARY KEY, status TEXT NOT NULL, details JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE inference_requests (id BIGSERIAL PRIMARY KEY, requested_window TEXT NOT NULL, result JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
