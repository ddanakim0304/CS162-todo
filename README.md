# CS162-todo

## Demo

[Demo Vidoe](https://www.loom.com/share/18e25546fe854ce8a474a53fd523203b?sid=f5fadb2c-5401-4b05-ad04-addaf2156bb1)


## Overview

This is a simple to-do application built using Flask, a Python web framework. It allows users to create accounts, log in, create to-do lists, add tasks to those lists, mark tasks as complete, move tasks between lists, and create subtasks. The application uses Flask-SQLAlchemy for database management and Flask-Login for user authentication.

## Features

-   User authentication (registration, login, logout)
-   Create and manage multiple to-do lists
-   Add, edit, and delete tasks
-   Create subtasks, up to 3 levels deep
-   Mark tasks as complete
-   Move tasks between lists
-   Collapse/expand tasks with subtasks
-   User-specific data isolation (users can only see and modify their own data)

## File Structure

-   `app.py`: Contains the main application logic, including:
    -   Flask app initialization
    -   Database models ([`User`](app.py), [`List`](app.py), [`Task`](app.py))
    -   Route definitions for:
        -   Home page ([`/`](app.py))
        -   Login ([`/login`](app.py))
        -   Registration ([`/register`](app.py))
        -   Logout ([`/logout`](app.py))
        -   Adding lists ([`/add_list`](app.py))
        -   Adding tasks ([`/add_task`](app.py))
        -   Completing tasks ([`/complete_task/<int:task_id>`](app.py))
        -   Toggling task collapse ([`/toggle_collapse/<int:task_id>`](app.py))
        -   Moving tasks ([`/move_task`](app.py))
        -   Deleting tasks ([`/delete_task/<int:task_id>`](app.py))
        -   Editing tasks ([`/edit_task/<int:task_id>`](app.py))
    -   Flask-Login user loader

-   `templates/`: Contains HTML templates for the application's views:
    -   `base.html`: Base template with common layout and navigation.
    -   `index.html`: Main page displaying to-do lists and tasks.
    -   `login.html`: Login form.
    -   `register.html`: Registration form.
    -   `task.html`: (Unused)

-   `test_app.py`: Contains unit tests for the application's functionality, including:
    -   User isolation tests
    -   Permission tests
    -   Task completion tests
    -   Task collapse tests
    -   Task moving tests

-   `requirements.txt`: Lists the Python packages required to run the application.

-   `.gitignore`: Specifies intentionally untracked files that Git should ignore.

-   `instance/`: Contains the SQLite database file (`todo.db`). This directory is ignored by Git.

## Dependencies

-   Flask
-   Flask-SQLAlchemy
-   Flask-Login
-   Werkzeug
-   SQLAlchemy

Install dependencies using pip:

```bash
pip install -r requirements.txt