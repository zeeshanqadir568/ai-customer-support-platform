from fastapi import FastAPI

app = FastAPI(
    title="AI Customer Support Platform",
    description="AI-powered customer support automation platform",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-customer-support-platform",
    }