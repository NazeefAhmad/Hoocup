from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from httpx import AsyncClient
from app.models.user import User
from app.utils.database import db
from app.utils.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/auth",
    tokenUrl="https://oauth2.googleapis.com/token",
)

@router.get("/auth/callback")
async def auth_callback(code: str):
    print(f"Received code: {code}")
    async with AsyncClient() as client:
        # Exchange the authorization code for an access token
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": "http://127.0.0.1:8081/auth/callback",
                "grant_type": "authorization_code",
            },
        )
        token_data = token_response.json()
        print("Token data:", token_data)
        access_token = token_data.get("access_token")

        # Use the access token to get user info
        user_info_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_info = user_info_response.json()
        

        # Create or update the user in the database
        user = User(
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info["picture"],
        )
        db.users.update_one({"email": user.email}, {"$set": user.dict()}, upsert=True)

        return {"message": "User authenticated", "user": user_info,"access_token": access_token}
