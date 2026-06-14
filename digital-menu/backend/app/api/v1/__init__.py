from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, restaurants, menu, devices, websocket, templates

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(restaurants.router)
api_router.include_router(menu.router)
api_router.include_router(devices.router)
api_router.include_router(websocket.router)
api_router.include_router(templates.router)


