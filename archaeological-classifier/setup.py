"""Setup script for Archaeological Classifier System."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip() for line in requirements_file.read_text().splitlines()
        if line.strip() and not line.startswith('#')
    ]

setup(
    name="archaeological-classifier",
    version="0.1.0",
    author="Enzo Cocca",
    author_email="enzo.ccc@gmail.com",  # Update with actual email
    description="Advanced 3D mesh analysis and formal taxonomy system for archaeological artifacts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/enzococca/BronzeAXE-AI",  # Update with actual URL
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "mypy>=1.5.0",
        ],
        "efa": [
            "pyefd>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "acs-cli=acs.cli:cli",
            "acs-server=acs.api.app:run_server",
            "acs-mcp=acs.mcp.server:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
