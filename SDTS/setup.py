from setuptools import setup, find_packages

setup(
    name="sdts",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PySide6>=6.0.0",
        "numpy>=1.20.0",
        "networkx>=2.5.0",
    ],
    extras_require={
        "dev": [
            "black>=21.0.0",
            "isort>=5.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
            "pytest>=6.0.0",
        ],
    },
    python_requires=">=3.8",
    author="SDTS Contributors",
    author_email="sdts@example.com",
    description="Schematic Design Tool Suite - A Python-based tool for creating and editing electronic circuit schematics",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/sdts",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
