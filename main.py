import os
import time
import threading
import asyncio
import requests
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import Response

app = FastAPI(title = "MLOps gateway", description = "This is a gateway for MLOps services.", version = "1.0.0")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

class ChatRequest(BaseModel):
    prompt: str

class TokensPerSecondResponse(BaseModel):
    total_duration: int
    prompt_eval_duration: int
    eval_duration: int
    eval_count: int

class MetricsResponse(BaseModel):
    tokens_per_second: float

TOKEN_PER_SECOND = Gauge(
    'tokens_per_second', 
    'Tokens generated per second'
)
    
@app.post("/chat")
async def chat_request(request: ChatRequest):
    try:
        # foward the req to native mac hardware
        response = requests.post(f"{OLLAMA_HOST}/api/generate", json={
                "model":"llama3.2:1b",
                "prompt": request.prompt,
                "stream": False
            },
            timeout=30
        )
        response.raise_for_status()

        tps = calculate_tokens_per_second(TokensPerSecondResponse(
            total_duration=response.json()["total_duration"],
            prompt_eval_duration=response.json()["prompt_eval_duration"],
            eval_duration=response.json()["eval_duration"],
            eval_count=response.json()["eval_count"]
        ))

        update_metrics(tps)

        return {
            "response": response.json()["response"],
            "tokens_per_second": tps
        }
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with OLLAMA service: {str(e)}" )
    
@app.get("/metrics")
async def metrics():
    """
    📈 Prometheus metrics endpoint
    This is where Prometheus scrapes our metrics
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
def calculate_tokens_per_second(item: TokensPerSecondResponse):
    if item.eval_duration == 0:
        return 0
    return round((item.eval_count / item.eval_duration) * 1_000_000_000, 2)

def update_metrics(tps: float):
    TOKEN_PER_SECOND.set(tps)