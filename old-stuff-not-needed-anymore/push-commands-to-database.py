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

def execute_query(connection, query, data):
    cursor = connection.cursor()
    try:
        cursor.execute(query, data)
        connection.commit()
        print("Query executed successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")

connection = create_database_connection()

# Define the INSERT query
insert_script_query = """
INSERT INTO scripts (name, title, info, command, admin_required)
VALUES (%s, %s, %s, %s, %s)
"""

# Script data to insert
scripts_data = [
  
    ("Home Page", "", 
     "Welcome to wincommander! This application helps you run various items on the list to fix common issues on Windows.\n\nUse the left panel to search for a specific item or select one from the list. The right panel displays details about the selected item, and you can run it by clicking the 'Run' button.\n\nRemember, not all Windows problems are the same. If one item doesn't work, try another one. We've included multiple items for some common issues to give you more options. For example, if the 'Reset audio' item doesn't work, you can try the 'Reset audio 2' item.\n\nMake sure to select the item that best matches your problem. If you're having audio issues, try one of the audio items. If you're unsure, don't worry! Just give it a try and see if it helps.\n\nThis tool is designed to be user-friendly, even for those who are not very tech-savvy. So don't worry if you're not a computer expert - we've got you covered! If you're still having trouble, feel free to email us or visit our website at wincommander.us.to for more help.\n\nFeel free to explore and enhance your Windows experience with wincommander!",
     None, False),
    ("windows-search-reset", "", 
     "This script restarts Windows Explorer.\n\nCommand: `taskkill /f /im explorer.exe && start explorer.exe`\n\nAdministrator Privileges: Required",
     "taskkill /f /im explorer.exe && start explorer.exe", True),
    ("Restart Internet Service", "", 
     "This script restarts the Internet service to fix common Internet issues in Windows.\n\nCommand: `net stop wuauserv && net start wuauserv`\n\nAdministrator Privileges: Required",
     "net stop wuauserv && net start wuauserv", True),
    ("Reset audio", "", 
     "This script fixes sound problems. It turns off and then turns on the sound services.\n\nCommand: `net stop audiosrv && net stop AudioEndpointBuilder && net start audiosrv && net start AudioEndpointBuilder`\n\nAdministrator Privileges: Required",
     "net stop audiosrv && net stop AudioEndpointBuilder && net start audiosrv && net start AudioEndpointBuilder", True),
    ("Reset audio 2", "", 
     "This is another script to fix sound problems. If 'Reset audio' didn't work, try this one. It just starts the sound services without turning them off first.\n\nCommand: `net start audiosrv && net start AudioEndpointBuilder`\n\nAdministrator Privileges: Required",
     "net start audiosrv && net start AudioEndpointBuilder", True),
    ("Start SSDP Service", "", 
     "This script starts the SSDP (Simple Service Discovery Protocol) service, which is used to discover UPnP devices on a network. Starting this service can help enable network discovery features.\n\nCommand: `net start ssdpsrv`\n\nAdministrator Privileges: Required",
     "net start ssdpsrv", True),
    ("Stop SSDP Service", "", 
     "This script stops the SSDP (Simple Service Discovery Protocol) service, which is used to discover UPnP devices on a network. Stopping this service can help troubleshoot network-related issues or reduce network traffic.\n\nCommand: `net stop ssdpsrv`\n\nAdministrator Privileges: Required",
     "net stop ssdpsrv", True),
]

# Insert script data into the database
for script in scripts_data:
    execute_query(connection, insert_script_query, script)

# Close the database connection
connection.close()
