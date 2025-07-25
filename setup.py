#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="warehouse-management-system",
    version="1.0.0",
    author="Developer",
    author_email="developer@example.com",
    description="نظام إدارة المخازن الشامل",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/warehouse-management",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Office/Business",
        "Topic :: Database",
    ],
    python_requires=">=3.7",
    install_requires=[
        "tkinter",
        "sqlite3",
        "datetime",
        "hashlib",
        "matplotlib",
        "pandas",
        "reportlab",
        "pillow",
        "ttkbootstrap",
    ],
    entry_points={
        "console_scripts": [
            "warehouse-management=main:main",
        ],
    },
)