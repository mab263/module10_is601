## 📝 Running Tests Locally

To run the tests locally, first install the project dependencies:

```bash
pip install -r requirements.txt
```

Make sure your PostgreSQL database is running and your test database environment variables are configured.

Then run the tests using:

```bash
pytest --cov=. --cov-report=term-missing
```

This runs the unit, integration, and end-to-end tests and displays the test coverage report.

## 🐳 Docker Hub

The Docker image for this project is available on Docker Hub:

[View Docker Hub Repository](https://hub.docker.com/r/mab263/module10_is601)


## 🗂️ Project Overview

This project enhances a FastAPI application by implementing a secure user management system using SQLAlchemy and Pydantic. It includes user creation and validation, password hashing and verification, and database integration with PostgreSQL. Unit and integration tests are used to verify functionality, data validation, and database operations. A CI/CD pipeline is configured with GitHub Actions to automatically run tests, build and scan the Docker image, and push the image to Docker Hub when the tests pass.
