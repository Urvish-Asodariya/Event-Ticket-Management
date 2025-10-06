from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controller import auth, passes, bookings, staff, admin, validation, zone
from contextlib import asynccontextmanager

@asynccontextmanager
async def startup_event():
    try:
        print( "Starting up..." )
    except Exception as e:
        print( "Error: " , e)


app = FastAPI(
    title="Pass Management API",
    description="API for managing event passes and bookings",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(zone.router, prefix="/zone", tags=["Zone"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(passes.router, prefix="/passes", tags=["Passes"])
app.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
app.include_router(staff.router, prefix="/staff", tags=["Staff"])
app.include_router(validation.router, prefix="/validate", tags=["Validation"])


async def root():
    return {
        "message": "Welcome to Navratri Pass Management API",
        "version": "1.0.0",
        "docs_url": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
