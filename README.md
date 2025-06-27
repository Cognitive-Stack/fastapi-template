# FastAPI Template API

API for FastAPI Template - A platform for managing your projects with AI.

## Features

*   **Authentication:** Secure user authentication using JWT.
*   **User Management:** Create, read, update, and delete users.
*   **Asynchronous:** Built with FastAPI for high performance.
*   **MongoDB:** Uses MongoDB as the database.
*   **RabbitMQ:** Uses RabbitMQ for message queuing.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

*   Python 3.12+
*   Poetry
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
    *   Install Python and Poetry if they are not already installed.
    *   Install project dependencies using Poetry.
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

## Project Structure

```
app/
├── __init__.py
├── main.py
├── controllers/
│   └── users.py
├── core/
│   └── settings.py
├── dependencies/
│   └── auth.py
├── middlewares/
│   └── cors_middleware.py
├── models/
│   ├── base.py
│   └── users.py
├── routers/
│   ├── auths.py
│   └── users.py
├── schemas/
│   ├── auths.py
│   └── users.py
├── utils/
│   ├── mongodb.py
│   ├── rabbitmq.py
│   └── superuser.py
└── workers/
    └── consumer.py
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
