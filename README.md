# ADA University
# Employee Registration Image Recognition

General application for the system is located here.


Starting server:
```python manage.py runserver 9000```

Connect PostgreSQL to Django

settings.py -> DATABASES -> change ```NAME``` (database name), ```USER``` (database username), ```PASSWORD``` (database setup password), ```HOST``` and ```PORT``` to appropriate credentials

then migrate the database to django using -> ```python manage.py migrate``` - if credentials are correct, this will create django's admin tables in your database

Then, run the ```subscription.py``` 


To create needed tables in PostgreSQL (if migration fails):

``` 
CREATE TABLE model_api_connection_employee (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL,
    surname VARCHAR(50) NOT NULL,
    fathers_name VARCHAR(50) NOT NULL,
    pincode VARCHAR(10) UNIQUE NOT NULL,
    department VARCHAR(50) NOT NULL
);
```
```
CREATE TABLE model_api_connection_attendance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID REFERENCES model_api_connection_employee(id),
    date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```
