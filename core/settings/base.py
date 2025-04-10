# DRF Spectacular Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'RBAC API Documentation',
    'DESCRIPTION': 'API documentation for the Role-Based Access Control system',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'SERVE_PUBLIC': True,
    'SERVE_AUTHENTICATION': None,
    'SERVE_PERMISSIONS': None,
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
} 