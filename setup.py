#!/usr/bin/env python3
"""
Setup script for Subtitle Creator for Guitar Backing Tracks
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="guitar-subtitle-creator",
    version="1.0.0",
    author="Guitar Subtitle Creator",
    description="Create SRT subtitles for guitar backing tracks with visual waveform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/guitar-subtitle-creator",
    packages=find_packages(),
    py_modules=["main"],
    install_requires=[
        "python-vlc>=3.0.0",
        "pysrt>=1.1.0",
        "numpy>=1.20.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "guitar-subs=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    include_package_data=True,
    package_data={
        "": ["buttons.list"],
    },
)
