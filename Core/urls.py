"""
URL configuration for Core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
import logging

logger = logging.getLogger(__name__)

# Debug logging
logger.info("Loading main URLs configuration")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include([
        path('', include('Apps.core.urls')),
        path('users/', include('Apps.users.urls', namespace='users')),  # Changed to have explicit prefix
        path('', include('Apps.entity.urls')),
        path('', include('Apps.contacts.urls')),
        path('', include('Apps.data_transfer.urls')),
    ])),
    path('api/v1/', include('Apps.project.urls', namespace='project')),  # Include project URLs with namespace
    path('api-auth/', include('rest_framework.urls')),  # Adds login to the browsable API
    
    # JWT endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

# Debug logging
logger.info("Main URLs registered:")
for pattern in urlpatterns:
    logger.info(f"Pattern: {pattern.pattern}")
    if hasattr(pattern, 'url_patterns'):
        for subpattern in pattern.url_patterns:
            logger.info(f"  Subpattern: {subpattern.pattern}")
            if hasattr(subpattern, 'url_patterns'):
                for subsubpattern in subpattern.url_patterns:
                    logger.info(f"    Subsubpattern: {subsubpattern.pattern}")
                    if hasattr(subsubpattern, 'name'):
                        logger.info(f"      Name: {subsubpattern.name}")
            if hasattr(subpattern, 'name'):
                logger.info(f"    Name: {subpattern.name}")
    if hasattr(pattern, 'name'):
        logger.info(f"  Name: {pattern.name}")

# Debug logging for project URLs
try:
    from Apps.project.urls import urlpatterns as project_urls
    logger.info("Project URLs loaded successfully:")
    for pattern in project_urls:
        logger.info(f"  Pattern: {pattern.pattern}")
        if hasattr(pattern, 'name'):
            logger.info(f"    Name: {pattern.name}")
        if hasattr(pattern, 'callback'):
            logger.info(f"    Callback: {pattern.callback}")
            if hasattr(pattern.callback, 'actions'):
                logger.info(f"      Actions: {pattern.callback.actions}")
except Exception as e:
    logger.error(f"Error loading project URLs: {e}")
