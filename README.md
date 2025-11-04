# FastAPI Template API

API for FastAPI Template - A platform for managing your projects with AI.

## Features

*   **Authentication:** Secure user authentication using JWT.
*   **User Management:** Create, read, update, and delete users.
*   **Chat Sessions:** Real-time chat with session management.
*   **Code Context:** Upload code repositories or zip files as context for AI chats.
*   **Asynchronous:** Built with FastAPI for high performance.
*   **MongoDB:** Uses MongoDB as the database.
*   **WebSocket Support:** Real-time communication capabilities.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

*   Python 3.12+
*   uv
*   Docker

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/fastapi-template.git
    cd fastapi-template
    ```

2.  **Run the installation script:**

    The `install.sh` script will:
    *   Install `poppler-utils`.
    *   Install Python and uv if they are not already installed.
    *   Install project dependencies using uv.
    *   Install Docker if it is not already installed.
    *   Pull and run MongoDB, Redis, and RabbitMQ Docker containers.

    ```bash
    bash install.sh
    ```

## Usage

To run the FastAPI application, use the following command:

```bash
make run
```

The application will be available at `http://127.0.0.1:8000`.

### Quick Links

- **Chat UI:** `http://127.0.0.1:8000/static/chat_sessions.html`
- **API Docs:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:

- **[Code Context Feature](docs/FEATURE_README.md)** - Complete guide to the code context feature
- **[Quick Start Guide](docs/QUICK_START_GUIDE.md)** - Step-by-step user guide
- **[Technical Documentation](docs/CODE_CONTEXT_FEATURE.md)** - API reference and implementation details
- **[All Documentation](docs/README.md)** - Full documentation index

## 🧪 Testing

Test files are organized in the `tests/` folder:

- **[Test Documentation](tests/README.md)** - Testing guide and instructions
- **Code Context Tests:** `python3 tests/test_context_feature.py`
- **WebSocket Tests:** `python3 tests/test_websocket.py`
- **Session Tests:** `bash tests/test_sessions.sh`

## Project Structure

```
fastapi-template/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── controllers/
│   │   └── users.py
│   ├── core/
│   │   └── settings.py
│   ├── dependencies/
│   │   └── auth.py
│   ├── middlewares/
│   │   └── cors_middleware.py
│   ├── models/
│   │   ├── base.py
│   │   ├── users.py
│   │   ├── chat_sessions.py
│   │   └── messages.py
│   ├── routers/
│   │   ├── auths.py
│   │   ├── users.py
│   │   ├── chat.py
│   │   └── chat_sessions.py
│   ├── schemas/
│   │   ├── auths.py
│   │   ├── users.py
│   │   ├── chat_sessions.py
│   │   └── messages.py
│   ├── static/
│   │   ├── chat.html
│   │   └── chat_sessions.html
│   └── utils/
│       ├── mongodb.py
│       └── superuser.py
├── docs/
│   ├── README.md
│   ├── FEATURE_README.md
│   ├── QUICK_START_GUIDE.md
│   └── CODE_CONTEXT_FEATURE.md
├── tests/
│   ├── README.md
│   ├── test_context_feature.py
│   └── test_websocket.py
├── docker-compose.yml
└── README.md
```

## Dependencies

The project uses the following dependencies:

*   **fastapi:** A modern, fast (high-performance), web framework for building APIs with Python 3.12+ based on standard Python type hints.
*   **uvicorn:** A lightning-fast ASGI server implementation.
*   **motor:** Asynchronous Python driver for MongoDB.
*   **python-jose:** A JOSE implementation in Python.
*   **passlib:** A library for hashing passwords.
*   **pydantic:** Data validation and settings management using Python type annotations.
*   **google-auth:** Google Authentication Library for Python.
*   **google-auth-oauthlib:** Google Authentication Library for Python with OAuthlib integration.
*   **pydantic-settings:** Pydantic settings management.
*   **python-multipart:** A streaming multipart parser for Python.
*   **aiohttp:** Asynchronous HTTP client/server framework.
*   **loguru:** A library which aims to bring enjoyable logging in Python.
*   **aio-pika:** An asynchronous AMQP client library for Python.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
