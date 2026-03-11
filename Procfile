release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
web: gunicorn volunteer.wsgi:application --log-file -
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python import_data.py data_dump.json
web: gunicorn volunteer.wsgi:application --log-file -