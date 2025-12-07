from pathlib import Path

import pytest


@pytest.fixture
def sample_actor() -> str:
    return """# Actor: User

## Description

A human user of the system.

## Notes

- Primary actor for most behaviors
"""


@pytest.fixture
def sample_behavior() -> str:
    return """# Behavior: Login

## Condition

- `@User` has valid credentials

## Description

The `@User` submits credentials to `#AuthComponent` which validates against `&UserCredentials` data.
On success, `!Dashboard View` is triggered.

## Outcome

- User is authenticated
- Session is created

## Notes

- Requires HTTPS
"""


@pytest.fixture
def sample_component() -> str:
    return """# Component: AuthComponent

## Description

Handles user authentication and session management.

## State

- authenticated: boolean
- session_token: string

## Events

- login_success
- login_failure
- logout

## Notes

- Uses JWT tokens
"""


@pytest.fixture
def sample_data() -> str:
    return """# Data: UserCredentials

## Description

User login credentials.

## Fields

- username: required string
- password: required string, hashed

## Notes

- Passwords are never stored in plain text
"""


@pytest.fixture
def sample_project() -> str:
    return """# Project: TestApp

## Description

A test application for DOG validation.

## Actors

- User
- Admin

## Behaviors

- Login
- Logout

## Components

- AuthComponent

## Data

- UserCredentials

## Notes

- This is a test project
"""


@pytest.fixture
def tmp_dog_dir(tmp_path: Path, sample_actor: str, sample_behavior: str) -> Path:
    """Create a temporary directory with sample .dog.md files."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "user.dog.md").write_text(sample_actor)
    (docs_dir / "login.dog.md").write_text(sample_behavior)

    return docs_dir
