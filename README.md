# License Management App - Run Instructions

## Prerequisites
- Python 3.8+
- PostgreSQL (Running on localhost:5432)
- PostgreSQL User: `postgres`, Password: `password` (Update in `config.py` if different)

## Installation

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Setup Database**:
    First, ensure your PostgreSQL server is running.
    Then run the helper script to create the database:
    ```bash
    python create_db.py
    ```
    (Or manually create a database named `license_db`)

    Then initialize the tables and default users:
    ```bash
    python init_db.py
    ```

## Running the Application

1.  **Start the Server**:
    ```bash
    uvicorn main:app --reload
    ```

2.  **Access the Dashboard**:
    Open [http://localhost:8000](http://localhost:8000) in your browser.

## User Roles & Credentials
There are 3 pre-configured users.

| Role | Username | Password |
| :--- | :--- | :--- |
| **Support** | `support` | `password` |
| **Accounts** | `accounts` | `password` |
| **License** | `license` | `password` |
