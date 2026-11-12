from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS middleware

## frontend URLs allowed to read responses (no trailing slashes)
FRONTEND_ORIGINS = [
    "http://localhost:5173"
]

## add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS, # use ["*"] to allow all public origins 
    allow_methods=["*"],
    allow_headers=["*"],
)

# health check
@app.get("/api/health")
def health():
    return {"status": "true"}