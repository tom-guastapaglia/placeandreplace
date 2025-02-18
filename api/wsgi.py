from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import streamlit.web as stw
import os

app = FastAPI()

@app.get("/")
async def root(request: Request):
    if os.environ.get("VERCEL_ENV") == "production":
        return stw.serve_streamlit_app("app.py")
    return HTMLResponse("""
    <html>
        <head><title>So'Managements - Gestionnaire de Documents</title></head>
        <body>
            <div id="root"></div>
            <script src="/_streamlit/streamlit.js"></script>
        </body>
    </html>
    """)

# Point d'entrée Vercel
def handler(request, context):
    return app(request, context) 