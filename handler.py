"""AWS Lambda handler for FastAPI application using Mangum."""

from mangum import Mangum

from app.presentation.main import app

handler = Mangum(app, lifespan="off")
