from database.mongodb import db

async def find_all_users():

    users = []

    cursor = db.users.find()

    async for user in cursor:

        user["_id"] = str(user["_id"])

        users.append(user)

    return users

async def insert_user(user: dict):

    result = await db.users.insert_one(user)

    return str(result.inserted_id)

async def find_user_by_username(username: str):

    return await db.users.find_one({
        "username": username
    })

async def find_user_by_oauth_state(state: str):

    return await db.users.find_one({
        "mal_oauth_state": state
    })

async def update_user(username: str, fields: dict):

    await db.users.update_one(
        {"username": username},
        {"$set": fields}
    )