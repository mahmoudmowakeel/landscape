import os
import requests
import supabase
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import UploadFile, File, HTTPException
from fastapi import Request
import uuid


# Load environment variables
load_dotenv()

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

# OAuth2 for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI()

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
    image_url: str
    description: str



@app.post("/signup")
def signup(user: SignupInput):
    response = supabase_client.auth.sign_up({
        "email": user.email,
        "password": user.password,
        "options": {
            "data": {
                "full_name": user.full_name
            }
        }
    })

    if response.error:
        raise HTTPException(status_code=400, detail=response.error.message)

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

@app.post("/password-reset")
def password_reset(email: str):
    response = requests.post(
        f"{SUPABASE_URL}/auth/v1/recover",
        json={"email": email},
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
    )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to send reset email")

    return {"message": "Password reset email sent. Please check your inbox."}


@app.post("/update-password")
def update_password(data: PasswordUpdateRequest):
    response = requests.put(
        f"{SUPABASE_URL}/auth/v1/user",
        json={"password": data.new_password},
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {data.access_token}",
            "Content-Type": "application/json"
        },
    )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to update password")

    return {"message": "Password updated successfully."}

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

    if role != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden")

    return {"message": "Welcome, Admin!"}


# 1️⃣ Add new image to category
@app.post("/admin/gallery/add")
def add_image(image: GalleryImageIn, role: str = Depends(get_current_user_role)):
    if role != "Admin":
        raise HTTPException(status_code=403, detail="Admins only")

    data = {
        "id": str(uuid.uuid4()),
        "category": image.category.lower().strip(),
        "image_url": image.image_url,
        "description": image.description
    }

    result = supabase_client.table("gallery_images").insert(data).execute()
    if result.error:
        raise HTTPException(status_code=400, detail=result.error.message)

    return {"message": "Image added successfully."}

@app.post("/admin/gallery/upload-image")
def upload_image(file: UploadFile = File(...)):
    from uuid import uuid4

    bucket_name = "gallery-images"
    file_ext = file.filename.split(".")[-1]
    file_path = f"{uuid4()}.{file_ext}"

    content = file.file.read()

    response = supabase_client.storage.from_(bucket_name).upload(
        file_path,
        content,
        {"content-type": file.content_type}
    )

    if response.get("error"):
        raise HTTPException(status_code=400, detail=response["error"]["message"])

    # Get public URL
    public_url = supabase_client.storage.from_(bucket_name).get_public_url(file_path)
    
    return {
        "message": "Image uploaded successfully.",
        "url": public_url
    }

# 2️⃣ Delete image by ID
@app.delete("/admin/gallery/delete/{image_id}")
def delete_image(image_id: str, role: str = Depends(get_current_user_role)):
    if role != "Admin":
        raise HTTPException(status_code=403, detail="Admins only")

    result = supabase_client.table("gallery_images").delete().eq("id", image_id).execute()
    if result.error:
        raise HTTPException(status_code=400, detail=result.error.message)

    return {"message": "Image deleted successfully."}

# 3️⃣ Get all images in a category
@app.get("/admin/gallery/{category}")
def get_images_by_category(category: str):
    result = supabase_client.table("gallery_images").select("*").eq("category", category.lower()).execute()

    if result.error:
        raise HTTPException(status_code=400, detail=result.error.message)

    return result.data