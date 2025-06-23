import psycopg2
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Database connection parameters from environment variables
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

def get_connection():
    """
    Establishes and returns a PostgreSQL database connection.
    Assumes database credentials are set in environment variables (POSTGRES_HOST, etc.).

    Returns:
        psycopg2.connection: A database connection object.
    Raises:
        Exception: If connection to the database fails.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("--- Database Connection: Successfully connected to PostgreSQL. ---")
        return conn
    except Exception as e:
        print(f"--- Database Connection: Error connecting to PostgreSQL: {e} ---")
        logging.exception("Database connection failed:")
        raise # Re-raise the exception to be handled upstream

def create_tables():
    """
    Creates the 'employees' and 'employee_skills' tables in the PostgreSQL database
    if they do not already exist.
    """
    print("--- Database Setup: Attempting to create tables... ---")
    conn = None
    curr = None
    try:
        conn = get_connection()
        curr = conn.cursor()
        # Create the employees table
        curr.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE -- Added UNIQUE constraint for employee names
            );
        """)
        # Create the employee_skills table
        curr.execute("""
            CREATE TABLE IF NOT EXISTS employee_skills (
                id SERIAL PRIMARY KEY,
                employee_id INT REFERENCES employees(id) ON DELETE CASCADE,
                tech TEXT NOT NULL,
                experience_years NUMERIC NOT NULL,
                UNIQUE (employee_id, tech) -- Prevents duplicate tech entries for the same employee
            );
        """)
        # Commit the changes
        conn.commit()
        print("--- Database Setup: Tables 'employees' and 'employee_skills' created successfully (if they didn't exist). ---")
    except Exception as e:
        print(f"--- Database Setup: An error occurred during table creation: {e} ---")
        logging.exception("Table creation failed:")
    finally:
        # Close the cursor and connection
        if curr:
            curr.close()
        if conn:
            conn.close()
            print("--- Database Setup: Database connection closed after table creation. ---")

if __name__ == "__main__":
    # This block allows you to run this script directly to set up your database tables.
    print("Running db_operations.py directly to create tables.")
    create_tables()

print("Database Operations: get_connection and create_tables functions defined.")