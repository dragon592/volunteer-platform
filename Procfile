release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
web: gunicorn volunteer.wsgi:application --log-file -