# Portal API

![Coverage Status](/coverage-badge.svg)

![https://github.com/eol-uchile/portal_api/actions](https://github.com/eol-uchile/portal_api/workflows/Python%20application/badge.svg)

# Install App

    docker-compose exec lms pip install -e /openedx/requirements/portal_api
    docker-compose exec lms python manage.py lms --settings=prod.production makemigrations portal_api
    docker-compose exec lms python manage.py lms --settings=prod.production migrate portal_api

## TESTS
**Prepare tests:**

- Install **act** following the instructions in [https://nektosact.com/installation/index.html](https://nektosact.com/installation/index.html)

**Run tests:**
- In a terminal at the root of the project
    ```
    act -W .github/workflows/pythonapp.yml
    ```
