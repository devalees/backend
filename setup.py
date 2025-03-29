from setuptools import setup, find_packages

setup(
    name="api",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'Django>=5.0.3',
        'djangorestframework>=3.16.0',
        'django-cors-headers>=4.7.0',
        'pillow>=11.1.0',
        'pyotp>=2.9.0',
        'qrcode>=8.0',
    ],
    extras_require={
        'test': [
            'factory-boy>=3.3.0',
            'faker>=24.1.0',
            'pytest>=8.0.2',
            'pytest-django>=4.8.0',
            'pytest-cov>=4.1.0',
            'pytest-xdist>=3.6.1',
        ],
    },
) 