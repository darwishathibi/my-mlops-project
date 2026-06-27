# MLOps Gateway

A FastAPI gateway in front of a local [Ollama](https://ollama.com) model that measures **tokens/second** per request and exposes it to Prometheus + Grafana.

```
curl /chat ──► gateway (FastAPI) ──► Ollama (host) ──► tps gauge
                                          │
                  Prometheus scrapes /metrics every 5s ──► Grafana
```

## Stack

| Service | Port | What |
|---------|------|------|
| gateway | 8000 | FastAPI app (`main.py`) |
| prometheus | 9090 | Scrapes `gateway:8000/metrics` every 5s |
| grafana | 3000 | Dashboards (login `admin`/`admin`); datasource + dashboard auto-provisioned |

## Prerequisites

Ollama running **on the host** with the model pulled:

```bash
ollama pull llama3.2:1b
ollama serve   # must listen on 0.0.0.0:11434 so containers can reach it
```

The gateway reaches it via `host.docker.internal` (wired in `docker-compose.yml`).

## Run

```bash
docker compose up --build
```

## Use

```bash
# Send a prompt — returns the response + measured tokens/second
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"hello"}'

# Prometheus metrics (the tokens_per_second gauge)
curl http://localhost:8000/metrics
```

Then open Grafana at http://localhost:3000 → **Dashboards → M4 Chip Inference Performance**. The Prometheus datasource and the dashboard are provisioned from files (see below) — no manual setup.

## Note on the "frozen" graph

`tokens_per_second` is a Prometheus **Gauge** — it holds the last measured value. With no traffic, Grafana draws a flat line (last reading repeated). That's correct, not a bug. To see it move, generate traffic:

```bash
while true; do
  curl -s -X POST http://localhost:8000/chat \
    -H 'Content-Type: application/json' \
    -d '{"prompt":"say one word"}' > /dev/null
  sleep 5
done
```

## Grafana provisioning

Loaded automatically at startup (mounted in `docker-compose.yml`):

```
grafana/
├── provisioning/
│   ├── datasources/prometheus.yml   # Prometheus datasource, fixed uid: prometheus
│   └── dashboards/provider.yml      # tells Grafana to load dashboards/*.json
└── dashboards/interface.json        # the "M4 Chip Inference Performance" dashboard
```

The dashboard references the datasource by the fixed `uid: prometheus`, so it works on any fresh container.

## Config

- `OLLAMA_HOST` — Ollama base URL (default `http://localhost:11434`; compose sets it to `host.docker.internal`)
- Model is hardcoded to `llama3.2:1b` in `main.py`
- Scrape interval: `prometheus.yml` (`5s`)
