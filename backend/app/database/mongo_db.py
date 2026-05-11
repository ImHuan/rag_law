from motor.motor_asyncio import AsyncIOMotorClient
import logging
from config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    _instance = None
    client: AsyncIOMotorClient = None
    db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    @classmethod
    async def connect(cls):
        try:
            cls.client = AsyncIOMotorClient(settings.MONGO_URI)
            await cls.client.admin.command("ping")
            cls.db = cls.client[settings.DB_NAME]
            logger.info("Connected to MongoDB Atlas successfully.")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise e

    @classmethod
    async def disconnect(cls):
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB.")

def get_db():
    if MongoDB.db is None:
        raise Exception("MongoDB is not initialized")
    return MongoDB.db
