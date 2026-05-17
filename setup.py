#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="lrc-tools",
    version="1.0.0",
    description="A CLI tool for embedding, extracting, cleaning, and identifying LRC lyrics in MP3 files",
    author="PaperNick",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "mutagen>=1.47.0",
    ],
    entry_points={
        "console_scripts": [
            "lrc_tools=lrc_tools:main",
            "lrc_tools-embed=lrc_embed:main",
            "lrc_tools-extract=lrc_extract:main",
            "lrc_tools-clean=lrc_clean:main",
            "lrc_tools-type=lrc_inspect:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Multimedia :: Sound/Audio",
    ],
)
