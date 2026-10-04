from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from ..deps import SettingsDep, UsersDep
from ..schemas import RegisterRequest, TokenResponse
from ..security import create_token, hash_password, verify_password

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(body: RegisterRequest, users: UsersDep) -> dict[str, str]:
    if not users.add(body.username, hash_password(body.password)):
        raise HTTPException(409, "Username taken")
    return {"username": body.username}


@router.post("/token", response_model=TokenResponse)
def token(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], users: UsersDep, s: SettingsDep
) -> TokenResponse:
    h = users.get_hash(form.username)
    if h is None or not verify_password(form.password, h):
        raise HTTPException(401, "Bad credentials", headers={"WWW-Authenticate": "Bearer"})
    tok, ttl = create_token(form.username, s)
    return TokenResponse(access_token=tok, expires_in=ttl)
