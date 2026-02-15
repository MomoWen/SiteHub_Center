#!/bin/bash
# SiteHub 质量自检脚本
echo "Running Mypy Type Check..."
.venv/bin/mypy src/
