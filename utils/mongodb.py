import motor.motor_asyncio

from .config import settings
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
try :
    db = client[settings.DB_NAME]
    print("Connected to MongoDB")
except Exception as e:
    print("Error: ", e)