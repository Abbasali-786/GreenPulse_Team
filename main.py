# main.py

import threading
import asyncio
from fastapi import FastAPI
from uagents import Bureau
# Make sure this import path is correct for your AgentOS agent
# It should point to the file that defines and exposes your agent for the Bureau
from agents.coach_agent_os import agent # Assuming 'agent' is the instance you want to add

app = FastAPI()

# Instantiate the Bureau
bureau = Bureau()

# Add your AgentOS agent instance to the Bureau
bureau.add(agent)

# --- CORRECTED WAY to integrate Bureau with FastAPI's event loop ---
# We use FastAPI's @app.on_event("startup") to ensure the Bureau starts
# within the existing event loop managed by FastAPI/Uvicorn.
@app.on_event("startup")
async def startup_event():
    # Start the bureau in the background using asyncio.create_task
    # This ensures it runs concurrently without blocking the FastAPI startup
    asyncio.create_task(bureau.run_async()) # ✅ Corrected: Call run_async and create a task

@app.get("/health")
async def health():
    """
    Simple health check endpoint for the FastAPI application.
    """
    return {"status": "ok"}

# To run this file:
# Make sure your virtual environment is activated: venv\Scripts\activate
# Then run: uvicorn main:app --reload --port 3000