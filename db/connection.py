
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
load_dotenv()

# Create a new client and connect to the server
client = MongoClient(os.getenv("MONGODB"), server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
# try:
#     client.admin.command('ping')
#     print("Pinged your deployment. You successfully connected to MongoDB!")
# except Exception as e:
#     print(e)
#     print("Failed to connect to MongoDB.")

# Generic function to execute queries
import uuid

# Generate a unique ID
  # uuid4() generates a random UUID

def run_query( db_name, collection_name, action, query=None, data=None):
    """
    Execute MongoDB queries dynamically.
    
    :param client: MongoClient instance
    :param db_name: Database name (string)
    :param collection_name: Collection name (string)
    :param action: 'find', 'insert', 'update', 'delete'
    :param query: MongoDB query filter (dict)
    :param data: Data for insert/update (dict)
    :return: Query result
    """
   
    db = client[db_name]
    collection = db[collection_name]

    if action == "find":
        return list(collection.find(query or {}))   # fetch all
    elif action == "insert":
        return collection.insert_one(data).inserted_id
    elif action == "update":
        return collection.update_one(query, {"$set": data}).modified_count
    elif action == "delete":
        return collection.delete_one(query).deleted_count
    elif action == "upsert_user":
        """
        Upsert a user:
        - Update if exists (except _id and created_at)
        - Insert if not exists (full document including _id and created_at)
    """
        if not query or not data:
            raise ValueError("query and data must be provided for upsert_user")
        
        existing = collection.find_one(query)
        
        if existing:
            # User exists → update everything except _id and created_at
            update_data = {k: v for k, v in data.items() if k not in ("_id", "created_at")}
            result = collection.update_one(query, {"$set": update_data})
            return existing["_id"]
        else:
            # User does not exist → insert full document
            result = collection.insert_one(data)
            return result.inserted_id
    else:
        raise ValueError("Unsupported action")
    
if __name__ == "__main__":
    # Example usage
    db_name = "student"
    collection_name = "linkedin_posts"
    action = "find"
    query = {"name": "John Doe"}
    unique_id = str(uuid.uuid4())
    data = {"id": unique_id, "name": "John Doe", "age": 30}

    result = run_query( db_name, collection_name, action, data=data)
    print(result)