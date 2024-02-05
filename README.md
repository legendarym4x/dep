### Homework 14

In this homework, we continue to refine our REST API application from homework 13.

Task:

     - Using Sphinx, we created the documentation for our project. To do this, docsrings were added to the necessary 
       functions and class methods in the main modules;
     - Covered the repository modules of our project with unit tests using Unittest framework;
     - We covered the authentication route from our project with functional tests using Pytest framework.

General requirements:

     All environment variables must be stored in an .env file. There should be no confidential data in the "clean" form
     inside the code;
     Docker Compose is used to run all services and databases in the application.

The authentication process, as well as updates, are performed in the Postman program, which is very convenient for 
this purpose.

To run the application, you must first start a Docker Compose containers (`docker compose up -d`) with postgres, Redis
and install the poetry virtual environment along with the necessary libraries.

Then you need to execute the following commands:

    - to create migrations:

        * alembic init migrations
        * alembic revision --autogenerate -m "Init"
        * alembic upgrade head

    - to launch the application:

        * uvicorn main:app --host localhost --port 8000 --reload

    - to run the pytest tests:

        * python -m pytest tests/ 