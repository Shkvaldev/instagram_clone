import os
import time
from pprint import pprint
from typing import Annotated, Dict, Any
from datetime import datetime
from loguru import logger
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword, ChallengeRequired, RecaptchaChallengeForm,
    FeedbackRequired, PleaseWaitFewMinutes, LoginRequired,
    ProxyAddressIsBlocked
)

# Project imports
from models import LoginAccount

app = FastAPI(
    title = "Instagram clonner",
    description="Web app for clonning followings and bookmarks"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log creation
log = logger
log.add(os.path.join("logs", f"clonner_{time.strftime('%H_%M_%S')}.log"), format="[ {time} ] [ {level} ] [ {message} ]", rotation="50 MB")

CLIENTS = {}

@app.post('/login')
def login(request: Request, auth_data: LoginAccount):
    """
    Logging in instagram account

    TODO!: Add session saving
    
    Returns:
        ```json
        {
            'id': 'account id for interacting with'
        }
        ```
    """
    log.debug(f"User with ip {request.client.host} is trying to log in instagram account") # type: ignore
    new_client = Client()
    new_client.delay_range = [1, 3]
    session_file = os.path.join("sessions", f"{auth_data.login}.json")
    if os.path.exists(session_file):
        try:
            # Loading session if exists
            new_client.load_settings(session_file)
            log.debug(f"User with ip {request.client.host} loaded session for '{auth_data.login}'") # type: ignore
        except Exception as e:
            log.debug(f"User with ip {request.client.host} failed to log in instagram account via saved session: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load session from file: {e}"
            )
    else:
        try:
            new_client.login(auth_data.login, auth_data.password)
            new_client.dump_settings(session_file)
            # TODO!: Save session
        except (BadPassword, RecaptchaChallengeForm, FeedbackRequired, PleaseWaitFewMinutes, LoginRequired, ChallengeRequired, ProxyAddressIsBlocked) as e:
            log.debug(f"User with ip {request.client.host} failed to log in instagram account: {e}") # type: ignore
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Bad credentails or proxy: {e}"
            )
    CLIENTS[auth_data.login] = new_client
    log.debug(f"New user with ip {request.client.host} logged in instagram account") # type: ignore
    return {"id": auth_data.login} 

@app.get('/account_info')
def get_followings(request: Request, login: str):
    """
    Retrives account info

    Args:
        login (str): User's login
    """
    log.debug(f"User with ip {request.client.host} is trying to get account info for '{login}'") # type: ignore
    if login not in CLIENTS.keys():
        log.debug(f"User with ip {request.client.host} failed to get account info for '{login}'") # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must be loginned before! Reffer to /login!"
        )
    # Getting info via API
    data =  CLIENTS[login].account_info().dict()
    log.debug(f"User with ip {request.client.host} got account info for '{login}'") # type: ignore
    return data

@app.get('/get_followings')
def get_followings(request: Request, login: str):
    """
    Retrives account's followings

    Args:
        login (str): User's login
    """
    log.debug(f"User with ip {request.client.host} is trying to get followings for '{login}'") # type: ignore
    if login not in CLIENTS.keys():
        log.debug(f"User with ip {request.client.host} failed to get followings for '{login}'") # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must be loginned before! Reffer to /login!"
        )
    # Getting info via API
    data =  CLIENTS[login].user_following(CLIENTS[login].user_id)
    print(f"[*] User's id is {CLIENTS[login].user_id}")
    log.debug(f"User with ip {request.client.host} got followings for '{login}'") # type: ignore
    return data