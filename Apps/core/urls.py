from django.urls import path, include
from .routers import api_router

urlpatterns = [
    # Include the central API router
    path('', include(api_router.urls)),
] 