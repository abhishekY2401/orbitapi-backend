import motor.motor_asyncio
from bson.objectid import ObjectId
from config import settings

MONGO_URL = settings.MONGO_URI

# establish a connection with mongodb
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)

database = client['orbit_api']
api_collection = database['api_specs']
report_collection = database['report']
