from fastapi import APIRouter

from . import bookings, rooms, spaces

api_router = APIRouter()

api_router.include_router(spaces.router, prefix="/spaces", tags=["Spaces"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])