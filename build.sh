#!/bin/bash
# Nettoyage
rm -rf __pycache__ .pytest_cache
find . -type d -name "__pycache__" -exec rm -r {} +

# Optimisation des dépendances
pip install --no-cache-dir -r requirements.txt

# Compression des assets
find static -type f -name "*.png" -exec convert {} -strip -quality 85 {} \; 