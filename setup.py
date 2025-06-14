#!/usr/bin/env python3
"""
Setup script for KnowledgeOps Agent
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
def read_requirements(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read version
def read_version():
    version_file = os.path.join("src", "knowledgeops", "__init__.py")
    with open(version_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"

setup(
    name="knowledgeops-agent",
    version=read_version(),
    author="KnowledgeOps Team",
    author_email="support@knowledgeops.com",
    description="Enterprise Knowledge Discovery Platform for Confluence and SharePoint",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mj3b/knowledgeops-agent",
    project_urls={
        "Bug Tracker": "https://github.com/mj3b/knowledgeops-agent/issues",
        "Documentation": "https://github.com/mj3b/knowledgeops-agent/docs",
        "Source Code": "https://github.com/mj3b/knowledgeops-agent",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Office/Business :: Groupware",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements("requirements/production.txt"),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.3.0",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
            "myst-parser>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "knowledgeops=knowledgeops.api.knowledgeops_app:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="knowledge management, confluence, sharepoint, ai search, enterprise search",
)

