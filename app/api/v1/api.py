from fastapi import APIRouter
from .endpoints import auth, listings, investors, blog, messages, users, utils

# Flat router - prefixes are in the endpoint files
api_router = APIRouter(redirect_slashes=False)

api_router.include_router(auth.router)
api_router.include_router(listings.router)
api_router.include_router(investors.router)
api_router.include_router(blog.router)
api_router.include_router(messages.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
