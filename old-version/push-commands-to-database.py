import mysql.connector
from mysql.connector import Error

def create_database_connection(host_name, user_name, user_password, db_name, port):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name,
            port=port
        )
        print("MySQL Database connection successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

def execute_query(connection, query, data):
    cursor = connection.cursor()
    try:
        cursor.execute(query, data)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# Replace with actual database details from database-setup.py
host = ""
username = ""
password = ""
database_name = ""
port = 3305

connection = create_database_connection(host, username, password, database_name, port)

# Define the INSERT query
insert_script_query = """
INSERT INTO scripts (name, title, info, command, admin_required)
VALUES (%s, %s, %s, %s, %s)
"""

# Script data to insert
scripts_data = [
    ("Stop SSDP Service", "", 
     "This script stops the SSDP (Simple Service Discovery Protocol) service, which is used to discover UPnP devices on a network. Stopping this service can help troubleshoot network-related issues or reduce network traffic.\n\nCommand: `net stop ssdpsrv`\n\nAdministrator Privileges: Required",
     "net stop ssdpsrv", True),
    ("Start SSDP Service", "", 
     "This script starts the SSDP (Simple Service Discovery Protocol) service, which is used to discover UPnP devices on a network. Starting this service can help enable network discovery features.\n\nCommand: `net start ssdpsrv`\n\nAdministrator Privileges: Required",
     "net start ssdpsrv", True),
    # ... add other script data here ...
]

# Insert script data into the database
for script in scripts_data:
    execute_query(connection, insert_script_query, script)

# Close the database connection
connection.close()
