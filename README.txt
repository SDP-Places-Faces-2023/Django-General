# ADA University
# Employee Registration Image Recognition

Starting server:
python manage.py runserver 9000

Connect PostgreSQL to Django

settings.py -> DATABASES -> change NAME (database name), USER (database username), PASSWORD (database setup password), HOST and PORT to appropriate credentials'

then migrate the database to django using -> python manage.py migrate - if credentials are correct, this will create django's admin tables in your database

Then, run the ```Subscription.py``` 
