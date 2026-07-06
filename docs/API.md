# API Reference

Base URL: `/api/v1`

## Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login with email/password |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Logout (requires auth) |
| GET | `/auth/me` | Get current user |
| POST | `/auth/forgot-password` | Request password reset |
| POST | `/auth/reset-password` | Reset password with token |

## Resources

| Resource | Endpoints |
|----------|-----------|
| Users | CRUD at `/users` (Admin) |
| Assignments | `/assignments` (Admin) |
| Customers | CRUD at `/customers` + QR at `/customers/{id}/qr` |
| Photos | List/upload at `/photos`, upload at `/photos/upload` |
| Sales | CRUD at `/sales`, export at `/sales/export/{format}` |
| Dashboard | GET `/dashboard` |
| Reports | GET `/reports/{type}?format=json\|csv\|excel\|pdf` |
| Search | GET `/search?q=...` |
| Portal | GET `/portal/{token}` (public) |

Full interactive documentation available at `/docs`.
