import time
import uuid
from pprint import pprint
from typing import Annotated, Dict, Any
from datetime import datetime
from loguru import logger
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword, ChallengeRequired, RecaptchaChallengeForm,
    FeedbackRequired, PleaseWaitFewMinutes, LoginRequired
)

# Project imports
from models import Account4Login

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
log.add(f"logs/clonner_{time.strftime('%H:%M:%S')}.log", format="[ {time} ] [ {level} ] [ {message} ]", rotation="50 MB")

CLIENTS = {}

@app.post('/login')
def login(request: Request, auth_data: Account4Login):
    """
    Logging in instagram account

    Returns:
        ```json
        {
            'id': 'account id for interacting with'
        }
        ```
    """
    log.debug(f"User with ip {request.client.host} is trying to log in instagram account") # type: ignore
    try:
        new_client = Client()
        new_client.delay_range = [1, 3]
        new_client.login(auth_data.login, auth_data.password)
    except (BadPassword, RecaptchaChallengeForm, FeedbackRequired, PleaseWaitFewMinutes, LoginRequired, ChallengeRequired):
        log.debug(f"User with ip {request.client.host} failed to log in instagram account") # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad credentails or proxy"
        ) 
    id = str(uuid.uuid4())
    CLIENTS[id] = new_client
    log.debug(f"New user with ip {request.client.host} logged in instagram account") # type: ignore
    return {"id": id} 
