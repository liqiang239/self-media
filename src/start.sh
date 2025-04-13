#!/bin/bash
python3 ./manage.py migrate
python3 ./manage.py migrate --database=api
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', '123456')" | python3 manage.py shell

#nohup celery -A celery_task worker -l info &
python3 manage.py runserver 0.0.0.0:8000

#daphne mj_client.asgi:application
