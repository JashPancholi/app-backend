from fastapi import APIRouter
from controllers.data_controller import (
    get_schedule, 
    get_items,
    get_events
)

data_router = APIRouter()

@data_router.get('/schedule')
async def schedule():
    return get_schedule()

@data_router.get('/items')
async def get_items_route():
    return get_items()

@data_router.get('/events')
async def events():
    return get_events()