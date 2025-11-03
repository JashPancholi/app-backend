from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

#Comparing passwd entered with the hashed passwd retrieved from the db
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

#Hashing a passwd enterd by user
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)