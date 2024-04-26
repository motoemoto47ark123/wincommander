import mysql.connector
from mysql.connector import Error

def swap_order_ids():
    try:
        # Establish the database connection
        connection = mysql.connector.connect(
            host="",
            user="",
            password="",
            database="",
            port=3305
        )

        # Create a new cursor
        cursor = connection.cursor()
        
        # Start transaction
        cursor.execute("START TRANSACTION;")

        # Get the order_ids for both rows
        cursor.execute(f"SELECT order_id FROM scripts WHERE id = %s;", (6,))
        order_id1 = cursor.fetchone()[0]

        cursor.execute(f"SELECT order_id FROM scripts WHERE id = %s;", (7,))
        order_id2 = cursor.fetchone()[0]

        # Swap the order_ids
        cursor.execute(f"UPDATE scripts SET order_id = %s WHERE id = %s;", (order_id2, 6))
        cursor.execute(f"UPDATE scripts SET order_id = %s WHERE id = %s;", (order_id1, 7))

        # Commit the transaction
        connection.commit()

        print("Order IDs swapped successfully.")
        
    except Error as e:
        # Rollback in case of error
        connection.rollback()
        print(f"Error: {e}")
    finally:
        # Closing the connection
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

# Call the function to swap IDs
swap_order_ids()
