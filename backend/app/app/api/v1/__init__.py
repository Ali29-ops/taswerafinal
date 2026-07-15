from fastapi import APIRouter

from app.api.v1 import assignments, attendance, auth, branches, customers, dashboard, hierarchy, leaderboard, packages, photos, portal, reports, sales, search, settings, targets, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(assignments.router)
api_router.include_router(attendance.router)
api_router.include_router(customers.router)
api_router.include_router(photos.router)
api_router.include_router(sales.router)
api_router.include_router(packages.router)
api_router.include_router(dashboard.router)
api_router.include_router(reports.router)
api_router.include_router(search.router)
api_router.include_router(portal.router)
api_router.include_router(settings.router)
api_router.include_router(targets.router)
api_router.include_router(hierarchy.router)
api_router.include_router(leaderboard.router)
api_router.include_router(branches.router)
