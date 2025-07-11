#!/usr/bin/env python3
"""
Enterprise API Test Automation Framework
Setup configuration for installation and distribution
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
def read_requirements(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="api-test-framework",
    version="1.0.0",
    author="Enterprise Test Team",
    author_email="test-team@company.com",
    description="Enterprise-grade API Test Automation Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/company/api-test-framework",
    packages=find_packages(exclude=['tests*', 'docs*']),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements('requirements.txt'),
    extras_require={
        'dev': read_requirements('requirements-dev.txt'),
        'security': ['bandit', 'safety'],
        'performance': ['locust>=2.0.0'],
        'monitoring': ['influxdb-client', 'grafana-api'],
    },
    entry_points={
        'console_scripts': [
            'api-test=framework.cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        'framework': [
            'config/*.yaml',
            'schemas/*.json',
            'templates/*.j2',
        ],
    },
    zip_safe=False,
)
