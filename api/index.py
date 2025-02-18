from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import streamlit as st
import subprocess
import os
import sys
from pathlib import Path

app = FastAPI()

# Montage des fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # Exécute l'application Streamlit en arrière-plan
    process = subprocess.Popen([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        "8501",
        "--server.address",
        "0.0.0.0",
        "--browser.serverAddress",
        request.base_url.hostname,
    ])
    
    # Retourne une page HTML qui intègre l'application Streamlit
    return """
    <html>
        <head>
            <title>So'Managements - Gestionnaire de Documents</title>
            <style>
                body, html {
                    margin: 0;
                    padding: 0;
                    height: 100%;
                    overflow: hidden;
                }
                iframe {
                    width: 100%;
                    height: 100%;
                    border: none;
                }
            </style>
        </head>
        <body>
            <iframe src="http://localhost:8501"></iframe>
        </body>
    </html>
    """

# Point d'entrée pour Vercel
def handler(request, context):
    return app(request, context) 