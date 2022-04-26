#!/bin/dash
pip install -e /openedx/requirements/portal_api

cd /openedx/requirements/portal_api
cp /openedx/edx-platform/setup.cfg .
mkdir test_root
cd test_root/
ln -s /openedx/staticfiles .

cd /openedx/requirements/portal_api

#openedx-assets collect --settings=prod.assets
DJANGO_SETTINGS_MODULE=lms.envs.test EDXAPP_TEST_MONGO_HOST=mongodb pytest portal_api/tests/tests_lms.py