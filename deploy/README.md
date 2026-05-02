# LankaGuide AI — Deployment

Production bring-up scripts for an AWS EC2 host (Ubuntu 22.04 LTS).
PRD reference: §13 Deployment Architecture, §14 Risks & Mitigations.

## Topology (default)

| Tier        | Process                                | Port / Socket            |
| ----------- | -------------------------------------- | ------------------------ |
| Frontend    | `next start` (systemd: `lankaguide-web`) | `127.0.0.1:3000`        |
| API         | Gunicorn (systemd: `lankaguide`)        | `unix:/run/gunicorn.sock`|
| Sentiment   | `manage.py start_sentiment_worker`      | systemd: `lankaguide-sentiment` |
| Aggregator  | `manage.py start_trend_aggregator`      | systemd: `lankaguide-trend-aggregator` |
| Cache       | Redis 7                                 | `127.0.0.1:6379`         |
| DB          | RDS MySQL 8 (external)                  | `db.amazonaws.com:3306`  |
| Vector DB   | ChromaDB (persistent local FS)          | `/var/data/chroma`       |
| Edge        | Nginx                                    | `:80, :443`              |

## Bring-up sequence

The repo is a mono-repo with `backend/` (Django), `frontend/` (Next.js) and
`deploy/` (these scripts). Both install scripts target the same checkout
under `/var/www/lankaguide`.

```bash
ssh ubuntu@<ec2-host>
sudo apt-get update -y
sudo apt-get install -y git
git clone https://github.com/your-org/lankaguide.git /tmp/repo
cd /tmp/repo

# 1) Backend, Nginx, Redis, systemd units
sudo bash deploy/install_backend.sh

# 2) Edit /var/www/lankaguide/backend/.env with real secrets, then:
sudo systemctl restart lankaguide

# 3) Populate the curated knowledge + DB:
sudo -u ubuntu bash -lc '
  cd /var/www/lankaguide/backend
  source venv/bin/activate
  python manage.py seed_database
  python manage.py ingest_knowledge_base
'

# 4) Frontend
sudo bash deploy/install_frontend.sh

# 5) HTTPS (Let's Encrypt)
sudo certbot --nginx -d lankaguide.lk -d www.lankaguide.lk \
     -m ops@lankaguide.lk --agree-tos --non-interactive
```

## Re-deploys

Both scripts accept `--redeploy` for fast, idempotent updates that
`git pull`, install deltas, run migrations / `next build`, and restart
the affected service without re-installing system packages.

```bash
sudo bash deploy/install_backend.sh  --redeploy
sudo bash deploy/install_frontend.sh --redeploy
```

## Operational checks

```bash
systemctl status lankaguide lankaguide-web \
                 lankaguide-sentiment lankaguide-trend-aggregator
journalctl -u lankaguide -f
curl -sf https://lankaguide.lk/healthz/
```
