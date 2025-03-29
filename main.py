import os
import requests
import supabase
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form, Request, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from pydantic import BaseModel
import uuid
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4




# Load environment variables
load_dotenv()

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

# OAuth2 for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
     allow_origins=["*"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)
# Define request body model
class SignupInput(BaseModel):
    full_name: str
    email: str
    password: str

class PasswordUpdateRequest(BaseModel):
    access_token: str
    new_password: str

# Pydantic models
class GalleryImageIn(BaseModel):
    category: str
    description: str

class PasswordResetRequest(BaseModel):
    email: str

@app.post("/signup")
def signup(user: SignupInput):
    try:
        response = supabase_client.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "full_name": user.full_name
                }
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected database error: {str(e)}")


    return {
        "message": "User created successfully. Please verify your email.",
        "user": response.user.email if response.user else None
    }


@app.post("/login")
def email_login(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    password = form_data.password

    response = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password},
        headers={
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        }
    )

    if response.status_code != 200:
        error_text = response.text.lower()
        if "email not confirmed" in error_text:
            raise HTTPException(status_code=401, detail="Please verify your email first.")
        else:
            raise HTTPException(status_code=401, detail="Invalid email or password")

    
    data = response.json()
    access_token = data.get("access_token")

    user_response = requests.get(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={"Authorization": f"Bearer {access_token}", "apikey": SUPABASE_KEY},
    )

    if user_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Error fetching user details")

    user = user_response.json()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user.get("user_metadata", {}).get("role", "user")
        }
    }


# --- 🔹 2️⃣ Google Login (Redirect) ---
@app.get("/auth/google")
def google_login():
    """
    Redirect users to Google login via Supabase.
    """
    google_url = f"{SUPABASE_URL}/auth/v1/authorize?provider=google"
    return {"login_url": google_url}


# --- 🔹 3️⃣ Google Callback (After Login) ---
@app.get("/auth/callback")
def google_callback(token: str):
    """
    Receive Supabase access token after Google login.
    """
    headers = {"Authorization": f"Bearer {token}", "apikey": SUPABASE_KEY}
    response = requests.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google login")

    user_data = response.json()
    user_id = user_data["id"]
    email = user_data["email"]
    role = user_data.get("user_metadata", {}).get("role", "user")  # Default to 'user'

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": email,
            "role": role
        }
    }



# @app.post("/password-reset")
# def password_reset(request: PasswordResetRequest):
#     try:
#         response = requests.post(
#             f"{SUPABASE_URL}/auth/v1/recover",
#             json={"email": request.email},
#             headers={
#                 "apikey": SUPABASE_KEY,
#                 "Content-Type": "application/json"
#             },
#         )

#         if response.status_code != 200:
#             raise HTTPException(status_code=400, detail="Failed to send reset email")

#         return {"message": "Password reset email sent. Please check your inbox."}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/password-reset")
def password_reset(request: PasswordResetRequest):
    try:
        redirect_url = "http://localhost:5173/change-password"  # 👈 Replace with your frontend reset page

        response = requests.post(
            f"{SUPABASE_URL}/auth/v1/recover",
            json={
                "email": request.email,
                "options": {
                    "redirectTo": redirect_url
                }
            },
            headers={
                "apikey": SUPABASE_KEY,
                "Content-Type": "application/json"
            },
        )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to send reset email")

        return {"message": "Password reset email sent. Please check your inbox."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_current_user_role(request: Request):
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token missing")

    # Verify token using Supabase
    user_info = supabase_client.auth.get_user(token)
    if user_info.user is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get role from metadata
    role = user_info.user.user_metadata.get("role", "User")
    return role

# --- 🔹 4️⃣ Admin Protected Route ---
@app.get("/admin")
def admin_route(token: str = Depends(oauth2_scheme)):
    """
    Protected route - Only accessible by admins.
    """
    headers = {"Authorization": f"Bearer {token}", "apikey": SUPABASE_KEY}
    response = requests.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_data = response.json()
    role = user_data.get("user_metadata", {}).get("role", "user")

    if role != "Admin":
        raise HTTPException(status_code=403, detail="Access forbidden")

    return {"message": "Welcome, Admin!"}


@app.post("/admin/gallery/add-image")
def add_image_with_upload(
    category: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
):
    bucket_name = "gallery-images"
    file_ext = file.filename.split(".")[-1]
    file_name = f"{uuid4()}.{file_ext}"
    file_bytes = file.file.read()

    # 1️⃣ Upload to Supabase Storage
    try:
        upload_response = supabase_client.storage.from_(bucket_name).upload(
            path=file_name,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected upload error: {str(e)}")

    image_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{file_name}"

    # 2️⃣ Insert metadata into Supabase DB
    try:
        db_response = supabase_client.table("gallery_images").insert({
            "id": str(uuid4()),
            "category": category.strip().lower(),
            "description": description.strip(),
            "image_url": image_url
        }).execute()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected database error: {str(e)}")

    return {
        "message": "Image uploaded and added to gallery successfully",
        "image_url": image_url
    }


from urllib.parse import urlparse
from fastapi import HTTPException

@app.delete("/admin/gallery/delete/{image_id}")
def delete_image(image_id: str):
    try:
        # 1. Get image URL from Supabase DB
        response = supabase_client.table("gallery_images").select("image_url").eq("id", image_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Image not found in database.")

        image_url = response.data["image_url"]

        # 2. Extract filename from URL
        file_name = image_url.split("/")[-1]  # e.g., acc71dc0-...jpg

        # 3. Delete from Supabase Storage (correct bucket!)
        delete_result = supabase_client.storage.from_("gallery-images").remove([file_name])


        # 4. Delete from Supabase DB
        supabase_client.table("gallery_images").delete().eq("id", image_id).execute()

        return {"message": "Image deleted from storage and database."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


# 3️⃣ Get all images in a category
@app.get("/admin/gallery/{category}")
def get_images_by_category(category: str):
    result = supabase_client.table("gallery_images").select("*").eq("category", category.lower()).execute()

    return result.data