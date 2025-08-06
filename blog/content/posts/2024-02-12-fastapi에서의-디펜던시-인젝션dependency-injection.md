---
author: Gunn Kim
date: '2024-02-12T04:26:00.000+00:00'
description: FastAPI에서 디펜던시 인젝션은 코드의 재사용성과 유지보수성을 크게 향상시키는 강력한 패턴입니다. 이 글에서는 디펜던시
  인젝션의 개념과 FastAPI에서의 구현 방법을 실제 예제와 함께 상세히 설명합니다. 인증, 데이터베이스 세션 관리, 권한 검증 등을 더 효율적으로
  처리하는 방법을 배워보세요.
draft: false
keywords: &id001
- Python
- Tech
- FastAPI
- Web Dev
lastmod: '2025-04-04T09:41:00.000Z'
notion_id: 0f718688-b48b-4a7c-86ac-c50604b2da39
slug: fastapi-dependency-injection-pattern-guide
subtitle: 클린 코드 작성을 위한 효과적인 API 설계 패턴 이해하기
summary: FastAPI에서 디펜던시 인젝션은 코드의 재사용성과 유지보수성을 크게 향상시키는 강력한 패턴입니다. 이 글에서는 디펜던시 인젝션의
  개념과 FastAPI에서의 구현 방법을 실제 예제와 함께 상세히 설명합니다. 인증, 데이터베이스 세션 관리, 권한 검증 등을 더 효율적으로 처리하는
  방법을 배워보세요.
tags: *id001
title: FastAPI에서의 디펜던시 인젝션(Dependency Injection)
---

```python
# 예시 코드 출처:https://blog.hops.pub/flask-to-fast-api

from fastapi import Header

async def verify_token(x_token: str = Header(...)):
    if x_token != 'fake-super-secret-token':
        raise HTTPException(status_code=401)
    return x_token

async def verify_token_get_user(
    token: str = Depends(verify_token),
    session: Session = Depends(session),
):
    return get_user_from_token(token, session)

auth_api = APIRouter(
    dependencies=[Depends(verify_token)],
)

@auth_api.get('/authorized-ping/')
async def authorized_ping():
    return 'pong'

@auth_api.get('/me/')
async def me(
    u: User = Depends(verify_token_get_user),
):
    return {'name': u.name}
```


디펜던시 인젝션(Dependency Injection)은 소프트웨어 설계 패턴 중 하나로, 한 컴포넌트의 의존성(즉, 다른 컴포넌트와의 연결)을 그 컴포넌트 내부가 아닌 외부에서 제공하는 방식을 말합니다. 이 패턴은 모듈 간의 결합도를 낮추고, 유연성과 재사용성을 높여줍니다. FastAPI에서 디펜던시 인젝션은 API의 다양한 부분에서 공통적으로 필요한 기능을 모듈화하고 재사용할 수 있게 해줍니다.

예를 들어, 여러 엔드포인트에서 토큰을 검증해야 할 경우, 해당 로직을 디펜던시로 만들어서 필요한 곳에 주입할 수 있습니다. 이 방식을 사용하면, 토큰 검증 로직을 중복으로 작성할 필요 없이, 해당 로직을 필요로 하는 모든 엔드포인트에서 이를 재사용할 수 있습니다. 이는 코드의 중복을 줄이고, 유지 보수를 쉽게 만들어줍니다.


```python
from fastapi import FastAPI, Header, HTTPException, Depends, APIRouter
from typing import Optional

# 비동기 함수로 토큰을 검증하는 디펜던시를 정의합니다. 이 함수는 요청 헤더에서 'x_token'을 추출합니다.
async def verify_token(x_token: str = Header(None)):
    # 토큰이 유효하지 않으면 401 상태 코드를 반환하는 HTTPException을 발생시킵니다.
    if x_token != 'fake-super-secret-token':
        raise HTTPException(status_code=401)
    # 토큰이 유효하면 토큰을 반환합니다.
    return x_token

# 이 함수는 'verify_token' 디펜던시를 사용하여 토큰을 검증하고, 
# 그 결과로 얻은 토큰을 사용하여 유저 정보를 가져오는 로직을 구현합니다.
# 여기서 'session'은 예시 코드이며, 실제로는 데이터베이스 세션을 생성하고 관리하는 로직이 필요합니다.
async def verify_token_get_user(
    token: str = Depends(verify_token),  # 'verify_token' 디펜던시를 통해 토큰을 검증합니다.
    session: Optional[Session] = Depends(None),  # 데이터베이스 세션 관리를 위한 디펜던시(여기서는 단순화를 위해 None으로 설정).
):
    # 'get_user_from_token' 함수를 사용하여 토큰으로부터 유저 정보를 가져옵니다.
    # 이 함수는 예시이며, 실제 구현이 필요합니다.
    return get_user_from_token(token, session)

# APIRouter 인스턴스를 생성하고, 'verify_token' 디펜던시를 이 라우터의 모든 경로에 자동으로 적용합니다.
auth_api = APIRouter(
    dependencies=[Depends(verify_token)],  # 모든 경로에 'verify_token' 디펜던시를 적용합니다.
)

# 'authorized_ping' 엔드포인트를 정의합니다. 이 엔드포인트는 'verify_token' 디펜던시를 통해 토큰 검증이 자동으로 이루어집니다.
@auth_api.get('/authorized-ping/')
async def authorized_ping():
    return 'pong'

# 'me' 엔드포인트를 정의합니다. 이 엔드포인트는 'verify_token_get_user' 디펜던시를 사용하여
# 토큰을 검증하고 유저 정보를 가져옵니다.
@auth_api.get('/me/')
async def me(
    u: User = Depends(verify_token_get_user),  # 'verify_token_get_user' 디펜던시를 통해 유저 정보를 가져옵니다.
):
    # 유저 정보에서 이름을 추출하여 반환합니다.
    return {'name': u.name}
```


제공된 예시에서는 `verify_token`이라는 비동기 함수가 토큰을 검증하는 디펜던시로 정의되어 있습니다. 이 함수는 `x_token`이라는 헤더를 매개변수로 받아, 토큰이 유효한지 검증합니다. 토큰이 유효하지 않으면 401 상태 코드와 함께 예외를 발생시킵니다. 이 디펜던시는 `APIRouter`의 디펜던시로 선언되어, 해당 라우터의 모든 엔드포인트에 자동으로 적용됩니다.

더 나아가, `verify_token_get_user` 함수는 `verify_token` 디펜던시를 사용하여 토큰을 검증한 뒤, 유저 정보를 가져오는 로직을 구현한 예입니다. 이러한 방식으로, 기본 디펜던시를 활용하여 더 복잡한 로직을 구현하는 새로운 디펜던시를 생성할 수 있습니다.

FastAPI의 디펜던시 인젝션 시스템은 코드의 재사용성과 테스트 용이성을 크게 향상시킵니다. 각종 설정, 데이터베이스 세션, 권한 검증 로직 등을 디펜던시로 만들어 관리함으로써, FastAPI 애플리케이션의 구조를 더욱 깔끔하고 유지 보수하기 쉽게 만들 수 있습니다.

웹소켓 엔드포인트의 구현 예시는 디펜던시 인젝션과는 직접적인 관련이 없지만, FastAPI의 또 다른 기능을 보여줍니다. FastAPI는 웹소켓 통신을 쉽게 구현할 수 있는 내장 지원을 제공합니다. 이를 통해 비동기적으로 클라이언트와 서버 간의 양방향 통신을 구현할 수 있으며, 이는 실시간 통신이 필요한 애플리케이션에 매우 유용합니다.

