import os
from azure.cosmos import CosmosClient
from dotenv import load_dotenv
import uuid

load_dotenv()

client = CosmosClient(
    os.getenv("COSMOS_ENDPOINT"),
    os.getenv("COSMOS_KEY")
)

database = client.get_database_client("agent-db")
container = database.get_container_client("sessions")


def create_session():
    session_id = str(uuid.uuid4())

    item = {
        "id": session_id,
        "session_id": session_id,
        "status": "created",
        "history": []
    }

    container.create_item(item)
    return session_id


def update_session(session_id, data):
    item = container.read_item(session_id, partition_key=session_id)

    item.update(data)

    container.upsert_item(item)


def get_session(session_id):
    return container.read_item(session_id, partition_key=session_id)
