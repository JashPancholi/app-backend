import pytest
from app.core.security import get_password_hash, verify_password

#checking if password can be hashed and verified
def test_password_hashing_and_verification():
    password = "My$ecretPassword123!"
    
    #Hash the password
    hashed_password = get_password_hash(password)
    
    #Compare original and hashed password, both should match
    assert verify_password(password, hashed_password) == True
    
    #Just checking if password and hashed_password are different for extra safety
    assert password != hashed_password

#Testing that a wrong password fails verification
def test_incorrect_password_verification():
    password = "Hello123"
    wrong_password = "WrongPassword"
    
    #Hash the password
    hashed_password = get_password_hash(password)
    
    #Compare original and hashed password, both should NOT match
    assert verify_password(wrong_password, hashed_password) == False

#Tests that the generated hash is an argon2 hash
def test_hash_is_argon2():
    password = "test_password"
    hashed_password = get_password_hash(password)
    assert hashed_password.startswith("$argon2id")