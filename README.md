User Authentication and Authorization API 

This project is a REST API for user authentication and authorization, based on custom JWT access token and UUID refresh token, built using Django and Django REST Framework. It supports user registration, authentication, token refresh, logout, and allows users to retrieve and update their personal information.

Installation

Clone this repository to your local machine.
Install dependencies using pip install -r requirements.txt.
Set up the database by running python manage.py migrate.
Start the development server with python manage.py runserver.

Usage

Registration: Users can register for an account by providing a username, email, and password.
Authentication: Users authenticate using their credentials to obtain access and refresh tokens.
Token Refresh: Users can refresh their access token using their refresh token.
Logout: Users can log out and invalidate their tokens.
Personal Information: Users can retrieve and update their personal information.

Tests

python manage.py test api.tests

Endpoints

/api/register/: POST method for user registration.
/api/login/: POST method for user authentication.
/api/refresh/: POST method for refreshing access token.
/api/logout/: POST method for logging out and invalidating tokens.
/api/me/: GET and POST methods for retrieving and updating personal information.

Security

Access tokens expire after 30 seconds by default.
Refresh tokens are UUIDs stored in the database, issued for 30 days by default.
Token-based authentication is used to secure endpoints.
