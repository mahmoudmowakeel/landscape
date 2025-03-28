# import secrets
# print(secrets.token_hex(32))  # Generates a 64-character (32-byte) secret key

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

hashed_password = pwd_context.hash("123")
print(hashed_password)  # Store this in the database instead of the plain password
