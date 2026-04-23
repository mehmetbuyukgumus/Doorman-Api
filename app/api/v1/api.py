from fastapi import APIRouter
from .endpoints import auth, listings, investors, blog, messages, users, utils

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(listings.router, tags=["listings"])
api_router.include_router(investors.router, prefix="/admin/investors", tags=["investors"])
api_router.include_router(blog.router, prefix="/blog-posts", tags=["blog"])
api_router.include_router(messages.router, prefix="/contact", tags=["messages"])
api_router.include_router(messages.router, prefix="/admin/contact-messages", tags=["messages-admin"])
api_router.include_router(users.router, prefix="/admin/users", tags=["users"])
api_router.include_router(utils.router, tags=["utils"])
