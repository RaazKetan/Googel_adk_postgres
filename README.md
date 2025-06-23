# 🤖 Employee Skill Assistant (Streamlit + Google ADK + Postgres)

This app is a smart chat interface powered by **Google Agent Development Kit (ADK)** and **Gemini 2.5**. It lets you add, update, delete, or view employee data (including tech stacks and experience) using natural language queries — no coding needed!

---

## 📸 Demo
![alt text](assets/image.png)
  
*Ask it things like:*  
- `"Add John who knows React (2 years) and Python (1 year)"`
- `"Update John's React experience to 3 years"`
- `"Delete employee John"`
- `"Show all employee data"`
---

## ✨ Features

* **Add Employees & Skills:** Easily add new employees and their associated tech skills with years of experience.
* **Update Skills:** Modify existing employee skills (e.g., update experience years for a specific tech).
* **Delete Employees:** Remove employees and their related skills from the database.
* **Query & Search:** Retrieve employee information and search for employees based on their tech stack.
* **Natural Language Interface:** Interact with the database using conversational English.

## 🚀 Getting Started

Follow these steps to set up and run the Employee Skill Assistant on your local machine.

### Prerequisites

Before you begin, ensure you have the following installed:
* ``` pip install -r requirements.txt ```
* **Python 3.9+**
* **pip** (Python package installer)
* **PostgreSQL Database Server**
* **pgAdmin 4** (Recommended for managing your PostgreSQL database visually)
* **Visual Studio Code (VS Code)** (Recommended IDE)
* **Google Gemini API Key**

### 1. Database Setup (PostgreSQL)

This application uses a PostgreSQL database to store employee and skill data.

#### 1.1 Install PostgreSQL

If you don't have PostgreSQL installed, download and install it from the official website:
[PostgreSQL Downloads](https://www.postgresql.org/download/)

During installation, you will be asked to set a password for the `postgres` superuser. Remember this password, as you'll need it later.

#### 1.2 Install pgAdmin 4 (Recommended)

pgAdmin 4 provides a user-friendly web interface for managing your PostgreSQL databases.
Download and install it from here: [pgAdmin Downloads](https://www.pgadmin.org/download/)

#### 1.3 Create the Database

You need to create a database named `employee_db` (or whatever you prefer, just ensure it matches your `.env` file).

**Using pgAdmin 4:**
1.  Open pgAdmin 4.
2.  In the left sidebar, expand "Servers" and click on "PostgreSQL X (Version Number)".
3.  Enter the `postgres` superuser password you set during installation to connect.
4.  Right-click on "Databases" -> "Create" -> "Database...".
5.  In the "General" tab, enter `employee_db` as the "Database" name.
6.  Click "Save".

**Using `psql` (Command Line):**
1.  Open your terminal or command prompt.
2.  Connect to PostgreSQL as the `postgres` superuser:
    ```bash
    psql -U postgres
    ```
    (Enter your `postgres` password when prompted)
3.  Create the database:
    ```sql
    CREATE DATABASE employee_db;
    \q
    ```

**Using `psql` (Command Line):**
1.  Connect to PostgreSQL as the `postgres` superuser:
    ```bash
    psql -U postgres
    ```
2.  Create the user and set a password:
    ```sql
    CREATE USER app_user WITH PASSWORD 'your_secure_password';
    ```
3.  Grant privileges on your database:
    ```sql
    GRANT ALL PRIVILEGES ON DATABASE employee_db TO app_user;
    \q
    ```

### 2. VS Code Setup (Optional but Recommended)

VS Code offers excellent extensions for Python and PostgreSQL.

1.  **Install Python Extension:** Search for "Python" by Microsoft in the Extensions view (`Ctrl+Shift+X` or `Cmd+Shift+X`) and install it.
2.  **Install PostgreSQL Extension:** Search for "PostgreSQL" by Microsoft and install it.
    * Once installed, you can click the Elephant icon in the Activity Bar (left sidebar).
    * Click the "+" button to add a new connection.
    * Enter the connection details for your `employee_db` (Host: `localhost`, User: `app_user` (or `postgres`), Password: `your_password`, Database: `employee_db`, Port: `5432`).
    * This allows you to browse your database tables directly within VS Code and run SQL queries.

### 3. Project Setup

1.  **Clone the Repository (if applicable) or create the project structure:**
    ```
    .
    ├── .env
    ├── app.py
    ├── core/
    │   ├── __init__.py
    │   ├── adk_config.py
    │   ├── db_operations.py
    │   └── adk_utils.py
    └── ui/
        ├── __init__.py
        └── streamlit_ui.py
    ```

2.  **Create a Virtual Environment (Recommended):**
    Navigate to your project's root directory in the terminal and run:
    ```bash
    python -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    * **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    * **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install Dependencies:**
    With your virtual environment activated, install the required Python packages:
    ```bash
    pip install streamlit google-generativeai python-dotenv psycopg2-binary google-adk
    ```
    *(Note: `google-adk` might have specific installation instructions; refer to its documentation if `pip install` fails.)*

### 4. Configure Environment Variables (`.env`)

Create a file named `.env` in the root directory of your project. Copy the following content and fill in your actual values:

```dotenv
# Google Generative AI Configuration (for Gemini API)
# Find your API Key at Google AI Studio: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
GOOGLE_API_KEY='YOUR_GOOGLE_GEMINI_API_KEY'

# If using Vertex AI (optional, leave blank otherwise)
# GOOGLE_GENAI_USE_VERTEXAI=True
# GOOGLE_CLOUD_PROJECT=your-gcp-project-id
# GOOGLE_CLOUD_LOCATION=us-central1 # e.g., us-central1

# PostgreSQL Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=employee_db
POSTGRES_USER=app_user # Or 'postgres' if you're using the default superuser
POSTGRES_PASSWORD=your_secure_password # The password for the user above
````

**Important:**
  * Replace `app_user` and `your_secure_password` with the credentials for the PostgreSQL user you created (or `postgres` and its password if you're using the default).
  * Ensure `POSTGRES_DB` matches the database name you created (`employee_db`).

### 5\. Initialize Database Tables

Before running the application, you need to create the necessary tables in your PostgreSQL database.

Navigate to your project's root directory in the terminal (with the virtual environment activated) and run:

```bash
python3 core/db_operations.py
```

This script will connect to your PostgreSQL database (using the credentials from `.env`) and create the `employees` and `employee_skills` tables if they don't already exist.

### 6\. Run the Application

Finally, start the Streamlit application:

```bash
streamlit run app.py
```

Your browser should automatically open to the Streamlit application (usually `http://localhost:8501`).

## 💬 How to Interact

Once the application is running, you can use the chat interface to manage employee data:

  * **Add an employee and their skills:**
    `Add John with 2 years React and 1 year Python`
  * **Update an employee's skill:**
    `Update John's React experience to 3 years`
  * **Delete an employee:**
    `Delete John`
  * **View an employee's skills:**
    `Show me John's skills`
    `What is Jane's tech stack?`
  * **Query for employees with certain skills:**
    `Who knows Python?`
    `Find employees with more than 2 years of Java experience`

Enjoy managing your employee skills with this AI assistant\!

```