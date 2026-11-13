# Authentication, Authorization, OAuth2 и JWT в FastAPI

> Полноценный учебный материал: теория простыми словами, объяснение терминов, работающий пример с FastAPI + Pydantic v2 + SQLAlchemy 2.x + SQLite, защита маршрутов, роли, истечение токена и практические задания.
>
> Стек примера: **Python 3.11+, FastAPI, PyJWT, pwdlib (Argon2), SQLAlchemy 2.x, SQLite**. Для первых занятий SQLite достаточно; позже можно перейти на PostgreSQL.

## Содержание

1. Authentication vs Authorization
2. Как работает вход в API
3. Пароль: хранение, хеширование, bcrypt, Passlib и Argon2
4. Что такое токен и Bearer
5. JWT: Header, Payload, Signature
6. OAuth2 в FastAPI
7. Dependency Injection для защиты маршрутов
8. Срок действия токенов: `exp`, UTC, `iat`, `nbf`
9. Структура учебного проекта
10. Установка и `.env`
11. Полный код проекта по файлам
12. Как запустить и проверить через Swagger и curl
13. Подробное объяснение пути запроса
14. Роли и разграничение прав
15. Refresh token, logout и отзыв токенов
16. Ошибки и безопасность
17. Частые вопросы
18. Практические задания и чеклист
19. Ссылки на официальную документацию

---

## 1. Authentication vs Authorization

**Authentication (аутентификация)** — проверка, *кто пользователь*. Пример: пользователь ввёл логин и пароль, сервер сравнил пароль с хешем и установил его личность.

**Authorization (авторизация / проверка прав доступа)** — проверка, *что этому пользователю разрешено*. Пример: пользователь уже вошёл, но удалить чужую книгу может только администратор.

| Ситуация | Проверка | Результат |
|---|---|---|
| Неверный пароль | Authentication | Вход запрещён: `401 Unauthorized` |
| JWT отсутствует или недействителен | Authentication | Доступ запрещён: `401 Unauthorized` |
| JWT верный, но роль `user` вместо `admin` | Authorization | Недостаточно прав: `403 Forbidden` |
| JWT верный, роль подходящая | Обе проверки | Доступ разрешён |

**Запомнить:** `401` означает проблему с подтверждением личности; `403` — личность известна, но прав не хватает. Название `401 Unauthorized` историческое и иногда путает.

## 2. Что происходит при входе

```text
[Клиент] -- POST /auth/login (username + password) --> [FastAPI]
                                                         |
                                                 Найти пользователя
                                                         |
                                                 Проверить хеш пароля
                                                         |
                                                  Создать JWT (exp)
                                                         |
[Клиент] <-- {access_token, token_type: "bearer"} -------+

[Клиент] -- GET /users/me, Authorization: Bearer <JWT> --> [FastAPI]
                                                           |
                                                Проверить подпись и exp
                                                           |
                                                   Найти пользователя
                                                           |
                                                  Вернуть профиль / 401
```

Почему пароль не отправляется снова в каждом защищённом запросе? После успешного входа клиент предъявляет токен. **Это не значит, что токен безопаснее хранить где угодно:** украденный действующий Bearer-токен позволяет выдавать себя за пользователя.

## 3. Password hashing: bcrypt, Passlib, Argon2

### 3.1. Почему нельзя хранить пароли обычным текстом

Плохо:

```python
users = [{"username": "ali", "password": "qwerty123"}]
```

Если база украдена, все пароли раскрыты. Нужно хранить **хеш пароля** — результат одностороннего алгоритма с солью и параметрами стоимости вычислений.

**Hashing ≠ encryption**:
- Шифрование (encryption) предполагает обратное расшифрование при наличии ключа.
- Хеширование пароля не предусматривает восстановление исходного пароля. Вход проверяется сравнением: `verify(введённый_пароль, сохранённый_хеш)`.
- Современные алгоритмы для паролей используют случайную **salt** (соль): поэтому два хеша одного пароля могут выглядеть по-разному.

### 3.2. Рекомендуемый новый вариант — `pwdlib` + Argon2

```bash
pip install 'pwdlib[argon2]'
```

```python
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

stored_hash = password_hash.hash("my-secret-password")
print(stored_hash)  # НЕ исходный пароль

assert password_hash.verify("my-secret-password", stored_hash)
assert not password_hash.verify("wrong-password", stored_hash)
```

Почему Argon2? Это современный алгоритм, предназначенный для хранения паролей; он настраивается по затратам памяти и времени. Актуальная документация FastAPI использует `pwdlib` + Argon2.

### 3.3. Что такое bcrypt и Passlib?

- **bcrypt** — алгоритм адаптивного хеширования паролей.
- **Passlib** — библиотека-обёртка, поддерживающая несколько алгоритмов и исторические форматы хешей.
- **Argon2** — другой, более современный алгоритм для хеширования паролей, рекомендуемый для новых реализаций в документации FastAPI.

Пример старого подхода, который можно встретить в существующих проектах:

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password_hash = pwd_context.hash("secret")
print(pwd_context.verify("secret", password_hash))
```

**Важно:** пример с Passlib демонстрирует API существующих проектов, **не является рекомендуемой конфигурацией нового приложения**. Некоторые сочетания версий Passlib/bcrypt несовместимы; для новых уроков используйте `pwdlib[argon2]`. Миграцию уже сохранённых хешей выполняют отдельно, с проверкой поддержки старых форматов. У bcrypt также есть особенности и ограничения на длину пароля в байтах; не нужно молча обрезать пароль.

### 3.4. Регистрация и вход — разные операции

- **Регистрация:** принять пароль → проверить допустимую длину → вычислить хеш → сохранить **только хеш**.
- **Вход:** найти пользователя → `verify()` введённого пароля → создать токен.
- Никогда не возвращать `hashed_password` или обычный пароль в API-ответе.

## 4. Token-based authentication и Bearer

**Токен** — строка, подтверждающая определённые полномочия на ограниченное время.

HTTP-заголовок защищённого запроса:

```http
GET /users/me HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Bearer** означает: тот, кто предъявил действующий токен, получает указанный доступ. Поэтому HTTPS и защита токена обязательны.

Токены бывают разными: случайные непрозрачные (opaque) строки с проверкой по серверному хранилищу и структурированные **JWT**. JWT — один из вариантов токена, а не синоним любой токенной аутентификации.

## 5. JWT: структура и подпись

JWT (JSON Web Token) выглядит как три фрагмента, разделённые точками:

```text
HEADER.PAYLOAD.SIGNATURE
```

- **Header** — информация о типе токена и алгоритме подписи (например, `HS256`).
- **Payload** — claims (утверждения): например, `sub` (ID пользователя), `exp` (срок истечения), `iat` (время выпуска).
- **Signature** — криптографическая подпись, помогающая обнаружить изменение Header/Payload.

Пример *содержимого* Payload:

```json
{
  "sub": "42",
  "exp": 1790000000,
  "iat": 1789998200
}
```

**JWT обычно не зашифрован!** Его содержимое можно декодировать без секретного ключа. Не помещайте в JWT пароль, персональные секреты или другие конфиденциальные сведения. Сервер **обязан проверять подпись** с заранее заданным допустимым алгоритмом и проверять срок действия.

Для `HS256` сервер подписывает и проверяет токен одним секретным ключом. В `jwt.decode()` нельзя брать список разрешённых алгоритмов из непроверенного заголовка токена.

## 6. OAuth2 в FastAPI: что означает каждая конструкция

**OAuth2** — стандартный фреймворк делегирования доступа. В обучающих примерах FastAPI распространён OAuth2 password flow: клиент передаёт логин и пароль приложению и получает Bearer access token.

При этом **password grant не рекомендуется для новых сторонних OAuth-интеграций** и отсутствует в OAuth 2.1; для внешних клиентов обычно выбирают **Authorization Code + PKCE** или OpenID Connect у identity provider. Здесь password flow используется как простой учебный способ реализовать вход в *собственное* API.

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
```

- `OAuth2PasswordBearer` **не создаёт и не проверяет JWT автоматически**. Он читает Bearer-токен из заголовка, интегрируется со схемой безопасности OpenAPI и обеспечивает работу кнопки **Authorize** в Swagger.
- `tokenUrl="auth/login"` — относительный путь, по которому Swagger сможет запросить токен; это не URL внешнего OAuth-провайдера.
- `OAuth2PasswordRequestForm` принимает данные как **`application/x-www-form-urlencoded`**, поля `username` и `password`, **не JSON**.
- Кнопка Swagger **Authorize** после входа добавляет заголовок `Authorization: Bearer ...` к запросам защищённых маршрутов.

## 7. Depends() и Dependency Injection

```python
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DB):
    ...

CurrentUser = Annotated[User, Depends(get_current_user)]

@app.get("/users/me")
def me(user: CurrentUser):
    return user
```

Смысл:
1. FastAPI вызывает `oauth2_scheme` и извлекает токен из заголовка.
2. Передаёт токен в `get_current_user`.
3. `get_current_user` проверяет JWT, загружает пользователя из базы и возвращает ORM-объект.
4. Эндпоинт получает готового пользователя как параметр `user`.

Если проверка завершится `HTTPException`, код защищённого маршрута вообще не исполнится. Так один механизм защиты можно использовать во множестве эндпоинтов.

## 8. Token expiration: exp, iat, nbf

| Claim | Что означает |
|---|---|
| `sub` | Subject — кого представляет токен, обычно ID пользователя (строкой) |
| `exp` | Expiration Time — после этого момента токен недействителен |
| `iat` | Issued At — когда токен выпущен |
| `nbf` | Not Before — не использовать раньше указанного времени |
| `iss` | Issuer — кто выпустил токен |
| `aud` | Audience — какому получателю токен предназначен |
| `jti` | JWT ID — уникальный идентификатор токена (полезен для отзыва) |

Даты для JWT нужно рассчитывать в **UTC**:

```python
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
expires_at = now + timedelta(minutes=30)
```

При проверке PyJWT автоматически проверяет `exp`, если он присутствует. Если наличие `exp` обязательно, дополнительно потребуйте его через `options={"require": ["exp", "sub"]}`. Для нескольких сервисов также проверяйте ожидаемые `issuer`/`audience`.

---

# 9–12. Полноценный учебный проект

Разработаем регистрацию, логин, личный профиль и роль администратора с SQLite и SQLAlchemy 2.x.

## 9. Структура

```text
fastapi_auth/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── security.py
├── dependencies.py
├── .env
└── requirements.txt
```

## 10. Установка

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows PowerShell
pip install fastapi 'uvicorn[standard]' sqlalchemy pyjwt 'pwdlib[argon2]' python-multipart pydantic-settings
```

Почему `python-multipart`? Он нужен для обработки формы, которую использует `OAuth2PasswordRequestForm`.

Создайте секрет (выполните локально):

```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

`.env`:

```dotenv
JWT_SECRET_KEY=ВСТАВЬТЕ_СЮДА_ВАШ_СЛУЧАЙНЫЙ_СЕКРЕТ
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Не коммитьте `.env` в Git; добавьте его в `.gitignore`. В production используется менеджер секретов или безопасные переменные окружения.

## 11. Полный код

### `database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///./auth.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # только SQLite
)

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)

def get_db():
    with SessionLocal() as session:
        yield session
```

- `engine` соединяет приложение с БД.
- `SessionLocal` создаёт отдельную ORM-сессию.
- `get_db()` передаёт сессию маршруту через `yield`, а после завершения закрывает её.
- `autoflush=False` отключает автоматический flush перед некоторыми запросами, **не перед commit**.
- `expire_on_commit=False` не помечает все уже загруженные атрибуты как устаревшие после commit.

### `models.py`

```python
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
```

`unique=True` запрещает одинаковые имена на уровне БД; `is_admin` для урока упрощает пример Authorization. В больших приложениях используют роли и отдельную таблицу permissions.

### `schemas.py`

```python
from pydantic import BaseModel, Field, ConfigDict

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)

class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    is_admin: bool
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

Зачем отдельные `RegisterRequest` и `UserResponse`? В запросе регистрации есть пароль, а в ответе его быть **не должно**. Не следует возвращать ORM-модель без явной Pydantic-схемы, если она содержит секреты.

### `security.py`

```python
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
```

Объяснение:
- `hash_password()` используется при регистрации.
- `verify_password()` используется при входе.
- `create_access_token()` подписывает токен, где `sub` — **ID** пользователя, `iat` — время выпуска, `exp` — истечение.
- JWT не хранит сессию на сервере: сервер может подтвердить подпись и срок действия, но для проверки актуальности пользователя всё равно обращается к БД.

### `dependencies.py`

```python
from typing import Annotated

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models import User
from security import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
DB = Annotated[Session, Depends(get_db)]

def credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DB,
) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
        user_id = int(payload["sub"])
    except (InvalidTokenError, ValueError, TypeError, KeyError):
        raise credentials_error()

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_error()
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

def require_admin(user: CurrentUser) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user

AdminUser = Annotated[User, Depends(require_admin)]
```

Очень важные строки:

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
```

Этот объект **вытаскивает строку токена** из `Authorization: Bearer ...`; он **не декодирует JWT**.

```python
CurrentUser = Annotated[User, Depends(get_current_user)]
```

Переиспользуемая зависимость, чтобы не писать проверку JWT в каждом роуте.

```python
AdminUser = Annotated[User, Depends(require_admin)]
```

Сначала вызывается `get_current_user`, а затем проверяется `is_admin`. Так реализуется **Authorization после Authentication**.

### `main.py`

```python
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database import Base, engine
from models import User
from schemas import RegisterRequest, UserResponse, TokenResponse
from security import hash_password, verify_password, create_access_token
from dependencies import DB, CurrentUser, AdminUser

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="FastAPI Authentication Tutorial", lifespan=lifespan)

@app.post("/auth/register", response_model=UserResponse, status_code=201)
def register(data: RegisterRequest, db: DB):
    existing_user = db.scalar(
        select(User).where(User.username == data.username)
    )
    if existing_user:
        raise HTTPException(status_code=409, detail="Username already exists")

    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
        is_active=True,
        is_admin=False,  # нельзя назначать admin из запроса регистрации
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already exists")
    db.refresh(user)
    return user

@app.post("/auth/login", response_model=TokenResponse)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DB,
):
    user = db.scalar(
        select(User).where(User.username == form.username)
    )
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    return TokenResponse(access_token=create_access_token(user.id))

@app.get("/users/me", response_model=UserResponse)
def read_me(current_user: CurrentUser):
    return current_user

@app.get("/admin/users", response_model=list[UserResponse])
def list_users(db: DB, admin: AdminUser):
    return db.scalars(select(User).order_by(User.id)).all()
```

**Замечание для преподавателя:** в `login()` при несуществующем пользователе проверка хеша не выполняется, а при существующем выполняется. В production это можно улучшить с помощью заранее подготовленного dummy-хеша, чтобы уменьшить различия времени ответа и риск перечисления пользователей. Также нужны rate limiting, аудит попыток входа, безопасная обработка секретов и полноценная настройка TLS.

## 12. Запуск и проверка

```bash
uvicorn main:app --reload
```

Перейдите на `http://127.0.0.1:8000/docs`.

### Шаг A: регистрация

`POST /auth/register` с JSON:

```json
{
  "username": "ali",
  "password": "my-strong-password"
}
```

Ответ `201`:

```json
{
  "id": 1,
  "username": "ali",
  "is_active": true,
  "is_admin": false
}
```

### Шаг B: вход

`POST /auth/login` — **form**, а не JSON:

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -d 'username=ali' \
  -d 'password=my-strong-password'
```

Пример структуры ответа:

```json
{
  "access_token": "<YOUR_JWT>",
  "token_type": "bearer"
}
```

### Шаг C: защищённый запрос

```bash
curl http://127.0.0.1:8000/users/me \
  -H 'Authorization: Bearer <YOUR_JWT>'
```

В Swagger удобно нажать **Authorize**, ввести логин и пароль и выполнить `GET /users/me`.

### Шаг D: проверка прав

`GET /admin/users` с обычным токеном вернёт `403`, потому что `is_admin=False`.

Чтобы протестировать роль администратора, **не добавляйте `is_admin` в запрос регистрации**. Назначайте роль отдельно через доверенный административный интерфейс/скрипт или заранее созданные тестовые данные.

---

## 13. Подробно: от запроса к ответу

**`POST /auth/register`:** Pydantic проверяет `username` и `password` → SQLAlchemy ищет дубликат → `pwdlib` хеширует пароль → ORM сохраняет пользователя → Pydantic `UserResponse` убирает секретные поля из ответа.

**`POST /auth/login`:** `OAuth2PasswordRequestForm` получает форму → SQLAlchemy находит пользователя → `verify_password()` сравнивает пароль с сохранённым хешем → `jwt.encode()` выдаёт подписанный токен с `exp`.

**`GET /users/me`:** `OAuth2PasswordBearer` читает заголовок → `jwt.decode()` проверяет подпись и срок → `db.get(User, id)` загружает текущего пользователя → эндпоинт возвращает профиль.

**`GET /admin/users`:** сначала всё то же, а затем `require_admin` проверяет роль. Если роль не подходит — `403`.

## 14. Authorization: роли, RBAC и права на объект

Проверять, что пользователь вошёл, **недостаточно**. Например, только владелец записи или администратор должны иметь возможность её изменить.

```python
@app.delete("/books/{book_id}")
def delete_book(book_id: int, current_user: CurrentUser, db: DB):
    book = db.get(Book, book_id)  # предполагается модель Book
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if book.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(book)
    db.commit()
    return {"message": "Deleted"}
```

Это **иллюстративный фрагмент**, не часть запускаемого `main.py`: потребуются модель `Book`, поле `owner_id` и импорт `HTTPException`.

Различайте:
- **Role-based (RBAC):** «только admin может смотреть список всех пользователей».
- **Object-level:** «пользователь может изменить только *свою* запись».
- **OAuth2 scopes:** набор объявленных прав токена; это ещё один инструмент, который можно изучить после базового примера.

## 15. Access token, refresh token, logout

В примере используется **только access token** с 30-минутным сроком жизни.

**Access token:** короткоживущий; отправляется к защищённым API.

**Refresh token:** отдельный токен для получения нового access token без повторного ввода пароля. Обычно живёт дольше, имеет отдельный тип и защищённое хранилище, требует **rotation**, управления отзывом и защиты от повторного использования. Не следует просто делать access token на 30 дней и называть это refresh token.

**Logout при JWT:** удалить токен у клиента **недостаточно для немедленного серверного отзыва**, если токен украден и его срок не истёк. Варианты решения:
1. Короткий срок действия access token.
2. Серверное хранилище отозванных `jti` с TTL.
3. Отзыв и rotation refresh token.
4. Проверка версии токена пользователя или других актуальных правил доступа.

Это дополнительная тема; в текущем учебном проекте logout и refresh не реализованы.

## 16. Частые ошибки и рекомендации по безопасности

| Ошибка | Почему плохо | Как правильно |
|---|---|---|
| Хранить пароль в `User.password` | При утечке раскрываются пароли | Хранить только адаптивный хеш |
| Писать `SECRET_KEY = "secret"` в коде | Простой известный ключ | Генерировать случайный секрет, хранить вне Git |
| Положить пароль в JWT Payload | JWT читается без ключа | В токен класть только нужные claims |
| Не проверять `exp` | Старые токены могут оставаться действительными | Требовать и проверять `exp` |
| Принимать алгоритм из токена | Риск неверной верификации | Явно задать `algorithms=["HS256"]` |
| Не проверять `is_active` | Заблокированный пользователь продолжит доступ | Проверять актуальный статус в БД |
| Принять `is_admin` из регистрации | Самостоятельная эскалация прав | Роль назначается доверенным процессом |
| Использовать токены по HTTP | Токен может быть перехвачен | В production использовать HTTPS |
| Не ограничивать попытки входа | Перебор паролей | Rate limiting, аудит и мониторинг |
| Отправлять токен куда попало | Утечка полномочий | Ограничить хранение/передачу, защищать от XSS/CSRF |

**Где хранить токен в браузере?** Любой способ имеет угрозы: `localStorage` доступен JS при XSS; `HttpOnly Secure SameSite` cookies снижают доступ JS, но требуют учёта CSRF и особенностей cookie-auth. Выбор зависит от архитектуры фронтенда. Для мобильного клиента используйте защищённое хранилище ОС.

**Серьёзный нюанс о JWT:** подпись гарантирует целостность и подлинность при правильном ключе, но **не гарантирует шифрование** и сама по себе не заменяет проверку прав на объект.

## 17. Частые вопросы

**Почему `OAuth2PasswordBearer` называется OAuth2, если я сам создаю JWT?**  
Он описывает OAuth2 Bearer-схему для HTTP/OpenAPI и извлекает токен. Генерация JWT, проверка подписи и поиск пользователя — ваша логика.

**Почему `/auth/login` принимает form-data, а не JSON?**  
Так устроен `OAuth2PasswordRequestForm`. Можно написать собственный JSON login endpoint, но стандартная интеграция OAuth2 password flow со Swagger использует форму.

**Что означает `sub`?**  
Subject — идентификатор того, для кого выпущен токен. В примере это строка с ID пользователя. Не используйте произвольный `sub`, присланный клиентом, без проверки личности.

**Разве `Depends()` вызывается на каждый запрос?**  
Зависимость вычисляется при обработке запроса; в пределах *одного* запроса одинаковая dependency обычно кешируется FastAPI. Новые HTTP-запросы получают собственную сессию БД.

**Что произойдёт после истечения JWT?**  
Проверка `jwt.decode()` завершится ошибкой, API вернёт `401`, пользователь должен снова войти или использовать отдельно реализованный refresh flow.

**В чём разница между `401` и `403`?**  
`401`: нет валидного подтверждения личности. `403`: личность подтверждена, но операция запрещена.

**Зачем БД, если у нас JWT?**  
JWT содержит утверждения, но не заменяет хранение пользователей, хешей паролей, статуса блокировки и ролей. Здесь актуальное состояние пользователя проверяется в БД.

**Может ли JWT содержать роль?**  
Да, но если роль изменится, старый токен может содержать устаревшее значение до окончания срока. Для чувствительных операций проверяйте актуальные права на сервере.

## 18. Практические задания

### Уровень 1 — основа

1. Реализовать регистрацию с `username`, `password`, `email` (email должен быть уникальным).
2. Разделить схемы `RegisterRequest`, `UserResponse`, `TokenResponse`.
3. Создать логин через `OAuth2PasswordRequestForm`.
4. Защитить `GET /users/me` через `Depends(get_current_user)`.
5. Сделать срок токена 5 минут и проверить ошибку `401` после истечения.

### Уровень 2 — проверка прав

6. Создать роли `user` и `admin` и запретить обычному пользователю `GET /admin/users`.
7. Создать модель `Book(owner_id)`; разрешить `PATCH/DELETE` только владельцу или администратору.
8. Добавить поле `is_active`; после блокировки запретить запросы с ранее выданным JWT.
9. Добавить ограничение числа попыток логина и логирование без записи паролей/токенов.

### Уровень 3 — дополнительно

10. Реализовать refresh tokens с ротацией и отзывом.
11. Добавить endpoint `/auth/logout`, использующий серверный механизм отзыва.
12. Добавить тесты: правильный логин, неправильный пароль, отсутствующий токен, истёкший токен, недостаточно прав.

### Чеклист знаний

- [ ] Объясняю разницу Authentication / Authorization
- [ ] Знаю, что означает `401` и `403`
- [ ] Умею хешировать пароль и проверять хеш
- [ ] Различаю bcrypt, Passlib и Argon2
- [ ] Понимаю Header / Payload / Signature JWT
- [ ] Знаю, зачем нужны `sub`, `exp`, `iat`
- [ ] Использую `OAuth2PasswordBearer` и `OAuth2PasswordRequestForm`
- [ ] Создаю и проверяю JWT через PyJWT
- [ ] Защищаю роуты через `Depends(get_current_user)`
- [ ] Проверяю права пользователя и владельца ресурса
- [ ] Умею объяснить, почему JWT не означает шифрование
- [ ] Понимаю, как работает истечение и отзыв токенов

## 19. Официальные источники

- FastAPI — OAuth2 with Password, Bearer and JWT: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- FastAPI — Simple OAuth2 with Password and Bearer: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
- FastAPI — Dependencies: https://fastapi.tiangolo.com/tutorial/dependencies/
- PyJWT — Usage: https://pyjwt.readthedocs.io/en/stable/usage.html
- pwdlib: https://frankie567.github.io/pwdlib/
- SQLAlchemy 2.x — ORM Quick Start: https://docs.sqlalchemy.org/en/20/orm/quickstart.html

---

> **Итог:** Authentication устанавливает личность пользователя; Authorization проверяет его права; password hashing защищает хранимые пароли; OAuth2 описывает способ выдачи и использования токена; JWT — подписанный формат токена; `Depends()` позволяет централизованно защищать маршруты; `exp` ограничивает срок действия. Для боевой системы нужны дополнительные механизмы защиты, перечисленные выше.
