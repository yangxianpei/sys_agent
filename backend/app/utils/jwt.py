from jose import jwt, ExpiredSignatureError, JWTError
from fastapi import HTTPException, Depends, Query, Request
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer

SECRET_KEY = "aaaaaaaanbnb"
ALGORITHM = "HS256"
security = HTTPBearer()  # 实例化


def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=1)

    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_token(request: Request, credentials=Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        request.state.user = payload
        return payload

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token已过期")

    except JWTError:
        raise HTTPException(status_code=401, detail="token无效")
