from setuptools import setup, find_packages

setup(
    name="api",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'django>=5.0',
        'djangorestframework>=3.14',
        'pytest-django>=4.5',
        'pytest>=7.0',
    ],
    python_requires='>=3.8',
) 