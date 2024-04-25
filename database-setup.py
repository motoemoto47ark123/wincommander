import mysql.connector
from mysql.connector import Error

def create_database_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host= "",
            user= "",
            passwd= "",
            database= "",
            port= 3305
        )
        print("MySQL Database connection successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

def create_table(connection, create_table_query):
    cursor = connection.cursor()
    try:
        cursor.execute(create_table_query)
        connection.commit()
        print("Table created successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# Define the create table query
create_scripts_table = """
CREATE TABLE IF NOT EXISTS scripts (
    id INT AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    info TEXT,
    command TEXT,
    admin_required BOOLEAN,
    PRIMARY KEY (id)
) ENGINE = InnoDB;
"""

# Establish a database connection and create the table
connection = create_database_connection("d09.h.filess.io", "wincommander_warmengine", "f3f664081bb66a0027ecc9a9550e7861f8b25833", "wincommander_warmengine")

# Only proceed if the connection was established
if connection is None:  # Fixed the error here
    print("Failed to connect to the database")
else:
    create_table(connection, create_scripts_table)

    # Close the connection
    connection.close()
