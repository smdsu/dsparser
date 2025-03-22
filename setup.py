"""
Setup script for dsparser package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dsparser",
    version="0.1.0",
    author="thesamedesu",
    author_email="thesamedesu@yandex.com",
    description="Discord messages parser and analyzer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thesamedesu/dsparser",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "beautifulsoup4>=4.9.0",
        "tqdm>=4.45.0",
    ],
    entry_points={
        "console_scripts": [
            "dsparser=dsparser.cli:main",
        ],
    },
) 