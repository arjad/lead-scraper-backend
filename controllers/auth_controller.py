import os
import boto3
from fastapi import HTTPException
from botocore.exceptions import ClientError
import hmac
import hashlib
import base64
import botocore
from botocore.config import Config

# Use python-dotenv to load env variables in main.py, so they are available here
COGNITO_REGION = os.getenv("COGNITO_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

# Initialize boto3 client without signing requests (no AWS credentials required) to avoid 'security token is invalid' errors
client = boto3.client(
    'cognito-idp', 
    region_name=COGNITO_REGION,
    config=Config(signature_version=botocore.UNSIGNED)
)

def get_secret_hash(username: str) -> str:
    if not COGNITO_CLIENT_SECRET:
        return None
    message = bytes(username + COGNITO_CLIENT_ID, 'utf-8')
    key = bytes(COGNITO_CLIENT_SECRET, 'utf-8')
    secret_hash = base64.b64encode(
        hmac.new(key, message, digestmod=hashlib.sha256).digest()
    ).decode()
    return secret_hash

import uuid

def signup(email: str, password: str):
    try:
        username = email
        kwargs = {
            'ClientId': COGNITO_CLIENT_ID,
            'Username': username,
            'Password': password,
            'UserAttributes': [
                {'Name': 'email', 'Value': email}
            ]
        }
        
        secret_hash = get_secret_hash(username)
        if secret_hash:
            kwargs['SecretHash'] = secret_hash
            
        response = client.sign_up(**kwargs)
        return {"message": "User signed up successfully. Please check your email for the confirmation code."}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response['Error']['Message'])

def confirm_signup(email: str, code: str):
    try:
        kwargs = {
            'ClientId': COGNITO_CLIENT_ID,
            'Username': email,
            'ConfirmationCode': code,
        }
        
        secret_hash = get_secret_hash(email)
        if secret_hash:
            kwargs['SecretHash'] = secret_hash
            
        response = client.confirm_sign_up(**kwargs)
        return {"message": "Email confirmed successfully. You can now sign in."}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response['Error']['Message'])

def resend_code(email: str):
    try:
        kwargs = {
            'ClientId': COGNITO_CLIENT_ID,
            'Username': email,
        }
        
        secret_hash = get_secret_hash(email)
        if secret_hash:
            kwargs['SecretHash'] = secret_hash
            
        response = client.resend_confirmation_code(**kwargs)
        return {"message": "Confirmation code resent successfully. Please check your email."}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response['Error']['Message'])

def signin(email: str, password: str):
    try:
        kwargs = {
            'AuthFlow': 'USER_PASSWORD_AUTH',
            'ClientId': COGNITO_CLIENT_ID,
            'AuthParameters': {
                'USERNAME': email,
                'PASSWORD': password,
            }
        }
        
        secret_hash = get_secret_hash(email)
        if secret_hash:
            kwargs['AuthParameters']['SECRET_HASH'] = secret_hash
            
        response = client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters=kwargs['AuthParameters']
        )
        
        auth_result = response.get('AuthenticationResult', {})
        if not auth_result:
            # Handle challenge responses (like NEW_PASSWORD_REQUIRED) if needed
            challenge = response.get('ChallengeName', '')
            if challenge == 'NEW_PASSWORD_REQUIRED':
                raise HTTPException(status_code=400, detail="New password required. Please login via AWS Hosted UI to reset, or implement the challenge flow.")
            raise HTTPException(status_code=400, detail=f"Authentication challenge required: {challenge}")
            
        return {
            "message": "Sign in successful",
            "access_token": auth_result.get('AccessToken'),
            "id_token": auth_result.get('IdToken'),
            "refresh_token": auth_result.get('RefreshToken')
        }
    except ClientError as e:
        raise HTTPException(status_code=401, detail=e.response['Error']['Message'])

def change_password(access_token: str, old_password: str, new_password: str):
    try:
        response = client.change_password(
            PreviousPassword=old_password,
            ProposedPassword=new_password,
            AccessToken=access_token
        )
        return {"message": "Password changed successfully"}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response['Error']['Message'])

def get_profile(access_token: str):
    try:
        response = client.get_user(AccessToken=access_token)
        attributes = {attr['Name']: attr['Value'] for attr in response.get('UserAttributes', [])}
        return {
            "username": response.get('Username'),
            "email": attributes.get('email')
        }
    except ClientError as e:
        raise HTTPException(status_code=401, detail=e.response['Error']['Message'])

def signout(access_token: str):
    try:
        response = client.global_sign_out(AccessToken=access_token)
        return {"message": "User signed out successfully"}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response['Error']['Message'])
