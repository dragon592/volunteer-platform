
web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python import_data.py data_dump.json && gunicorn volunteer.wsgi:application --log-file -