# Portal API
![https://github.com/eol-uchile/portal_api/actions](https://github.com/eol-uchile/portal_api/workflows/Python%20application/badge.svg)

# Install App

    docker-compose exec lms pip install -e /openedx/requirements/portal_api

## TESTS
**Prepare tests:**

    > cd .github/
    > docker-compose run lms /openedx/requirements/portal_api/.github/test_lms.sh
