from fastapi import FastAPI

app = FastAPI(
  title="ReturnGuard API",
  description="Governed e-commerce return and refund review system",
  version="0.1.0",
)

@app.get("/health",tags=["Health"])
async def health_check() -> dict[str,str]:
  """Report whether the API process is responding"""
  return {
    "status" : "ok",
    "service" : "returnguard-api",
  }