import psycopg2
from psycopg2 import OperationalError

def create_database_connection():
    connection = None
    try:
        connection = psycopg2.connect(
            ""
        )
        print("PostgreSQL Database connection successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection

def create_table(connection, create_table_query):
    cursor = connection.cursor()
    try:
        cursor.execute(create_table_query)
        connection.commit()
        print("Table created successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")

# Define the create table query
create_scripts_table = """
CREATE TABLE IF NOT EXISTS scripts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    info TEXT,
    command TEXT,
    admin_required BOOLEAN
);
"""

# Establish a database connection and create the table
connection = create_database_connection()

# Only proceed if the connection was established
if connection is None:
    print("Failed to connect to the database")
else:
    create_table(connection, create_scripts_table)

    # Close the connection
    connection.close()
