# Deployment Guide

## Docker Compose (Recommended)

The entire stack runs with a single command:

```bash
docker compose up --build
```

Services:

| Service | Internal Port | Description |
|---------|--------------|-------------|
| db | 5432 | PostgreSQL 16 |
| backend | 8000 | FastAPI API |
| frontend | 3000 | Next.js app |
| nginx | 80 | Reverse proxy |

## Production Checklist

- [ ] Change `SECRET_KEY` and `JWT_SECRET_KEY` to strong random values
- [ ] Set `APP_ENV=production` and `DEBUG=false`
- [ ] Configure S3 storage (`STORAGE_TYPE=s3`)
- [ ] Set up SMTP for password reset emails
- [ ] Enable HTTPS with SSL certificates
- [ ] Configure firewall (allow 80, 443)
- [ ] Set up database backups
- [ ] Configure log rotation

## SSL with Certbot

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

Update `FRONTEND_URL` and `CORS_ORIGINS` to use your production domain.

## S3 Storage

Set these environment variables for production file storage:

```
STORAGE_TYPE=s3
S3_ENDPOINT_URL=https://your-s3-endpoint
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET_NAME=photo-printing
S3_REGION=us-east-1
```

Compatible with AWS S3, MinIO, DigitalOcean Spaces, and other S3-compatible services.
