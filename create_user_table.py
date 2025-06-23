import psycopg2
from dotenv import load_dotenv
import os
#Load environment variables from .env file
load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

def create_user_table():
    try:
        #Connect to the PostgreSQL database
        conn = psycopg2.connect(
            host = DB_HOST,
            port = DB_PORT,
            dbname = DB_NAME,
            user = DB_USER,
            password = DB_PASSWORD  
        )
        curr = conn.cursor()
        #Create the users table
        curr.execute("""
                     CREATE TABLE IF NOT EXISTS employees (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL
                        );
                        CREATE TABLE employee_skills (
                            id SERIAL PRIMARY KEY,
                            employee_id INT REFERENCES employees(id) ON DELETE CASCADE,
                            tech TEXT NOT NULL,
                            experience_years NUMERIC NOT NULL
                            );
                     """)
        #Commit the changes
        conn.commit()
        print("Tables created successfully")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        #Close the cursor and connection
        if curr:
            curr.close()
        if conn:
            conn.close()
if __name__ == "__main__":
    create_user_table()
# This script creates the 'employees' and 'employee_skills' tables in the PostgreSQL
# database. The 'employees' table has an 'id' and 'name', while the 'employee_skills' table
# has an 'id', 'employee_id' (which references the 'employees' table), 'tech', and 'experience_years'.
# The script uses psycopg2 to connect to the database and execute the SQL commands.
# It also uses dotenv to load environment variables for database connection parameters.
# The tables are created only if they do not already exist. If an error occurs during the process,
# it will print the error message. Finally, it ensures that the cursor and connection are closed properly.