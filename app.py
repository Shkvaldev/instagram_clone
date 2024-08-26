import os
import time
from pprint import pprint
from typing import Annotated, Dict, Any, List
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
def account_info(request: Request, login: str):
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
    # Getting account info
    try:
        data =  CLIENTS[login].account_info().dict()
    except Exception as e:
        log.debug(f"User with ip {request.client.host} failed to get account info for '{login}': {e}") # type: ignore
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get info from API - connect with admin to overcome this problem: {e}"
        )
    log.debug(f"User with ip {request.client.host} got account info for '{login}'") # type: ignore
    return data

@app.get('/get_followings')
def get_followings(request: Request, login: str):
    """
    Retrives account's followings

    Args:
        login (str): User's login
    """
    session_file = os.path.join("sessions", f"{login}.json")
    log.debug(f"User with ip {request.client.host} is trying to get followings for '{login}'") # type: ignore
    if login not in CLIENTS.keys():
        log.debug(f"User with ip {request.client.host} failed to get followings for '{login}'") # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must be loginned before! Reffer to /login!"
        )
    # Getting followings
    try:
        del CLIENTS[login]
        client = Client()
        client.load_settings(session_file)
        CLIENTS[login] = client
        data = CLIENTS[login].user_following(CLIENTS[login].user_id)
    except Exception as e:
        log.debug(f"User with ip {request.client.host} failed to get followings for '{login}': {e}") # type: ignore
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get info from API - connect with admin to overcome this problem: {e}"
        )
    log.debug(f"User with ip {request.client.host} got followings for '{login}'") # type: ignore
    return data

@app.post('/add_followings')
def add_followings(request: Request, login: str, following_ids: List[str]):
    """
    Adds followings

    Args:
        login (str): User's login
        following_ids (List[str]): Array of media ids
    """
    log.debug(f"User with ip {request.client.host} is trying to add followings for '{login}'") # type: ignore
    if login not in CLIENTS.keys():
        log.debug(f"User with ip {request.client.host} failed to add followings for '{login}'") # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must be loginned before! Reffer to /login!"
        )
    if len(following_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=f"There is no any following in request - fill 'following_ids' field"
        )
    result = {
        'success': [],
        'waiting': [],
        'fail': []
    }
    for following_id in following_ids:
        try:
            if CLIENTS[login].user_follow(following_id):
                result['success'].append(following_id)
            else:
                raise ValueError("Check logs to get more info")
        except FeedbackRequired:
            result['waiting'].append(following_id)
        except Exception as e:
            log.error(f"Failed to add following '{following_id}' to collection for '{login}': {e}")
            result['fail'].append(following_id)
    return result

@app.get('/get_collections')
def get_collections(request: Request, login: str):
    """
    Retrives account's collections

    Args:
        login (str): User's login
    """
    log.debug(f"User with ip {request.client.host} is trying to get collections for '{login}'") # type: ignore
    if login not in CLIENTS.keys():
        log.debug(f"User with ip {request.client.host} failed to get collections for '{login}'") # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must be loginned before! Reffer to /login!"
        )
    # Getting collections
    try:
        collections = CLIENTS[login].collections()
        data = [{'id': collection.id, 'name': collection.name, 'amount': collection.media_count, 'medias': CLIENTS[login].collection_medias(collection_pk=collection.id, amount=0)} for collection in collections]
    except Exception as e:
        log.debug(f"User with ip {request.client.host} failed to get collections for '{login}': {e}") # type: ignore
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get info from API - connect with admin to overcome this problem: {e}"
        )
    log.debug(f"User with ip {request.client.host} got collections for '{login}'") # type: ignore
    return data

@app.post('/add_medias_to_collection')
def add_medias(request: Request, login: str, media_ids: List[str]):
    """
    Adds medias to collection

    Args:
        login (str): User's login
        media_ids (List[str]): Array of media ids
    """
    log.debug(f"User with ip {request.client.host} is trying to add medias to collections for '{login}'") # type: ignore
    if login not in CLIENTS.keys():
        log.debug(f"User with ip {request.client.host} failed to add medias to collections for '{login}'") # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must be loginned before! Reffer to /login!"
        )
    if len(media_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=f"There is no any media in request - fill 'media_ids' field"
        )
    result = {
        'success': [],
        'fail': []
    }
    for media_id in media_ids:
        try:
            if CLIENTS[login].media_save(media_id):
                result['success'].append(media_id)
            else:
                raise ValueError("Check logs to get more info")
        except Exception as e:
            log.error(f"Failed to add media '{media_id}' to collection for '{login}': {e}")
            result['fail'].append(media_id)
    return result