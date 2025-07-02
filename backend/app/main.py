from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import os
from .routers import budget, bill, compare
from .database import engine, Base

# VPC CONFIGURATION NEEDED FOR AWS LAMBDA:
# - Lambda must be in same VPC as RDS
# - Security group must allow outbound 5432 to RDS security group  
# - VPC endpoints for internet access (or NAT Gateway)

# ENVIRONMENT VARIABLES NEEDED:
# - DATABASE_URL (from AWS Secrets Manager)
# - CORS_ORIGINS (for frontend domain)

app = FastAPI(
    title="Federal Budget Dashboard API",
    description="API for visualizing U.S. federal budget and legislative changes",
    version="1.0.0"
)

# CORS configuration for frontend
origins = [
    "http://localhost:3000",  # Local React development
    "https://your-vercel-domain.vercel.app",  # Production frontend
]

# Add CORS_ORIGINS from environment if available
if cors_origins := os.getenv("CORS_ORIGINS"):
    origins.extend(cors_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(budget.router, prefix="/api", tags=["budget"])
app.include_router(bill.router, prefix="/api", tags=["bill"])
app.include_router(compare.router, prefix="/api", tags=["compare"])

@app.get("/")
async def root():
    return {"message": "Federal Budget Dashboard API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# AWS Lambda handler
lambda_handler = Mangum(app) 