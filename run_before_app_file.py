
import mysql.connector

# Connect to Clever Cloud database
conn = mysql.connector.connect(
    host="bt50vekxtlpwanbpzo6n-mysql.services.clever-cloud.com",
    user="uybdk7ycpidf4axw",
    password="ke39xPKLUbqr6PBdH351",
    database="bt50vekxtlpwanbpzo6n"
)


cursor = conn.cursor()

# Create the `users` table
create_table_query = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL
);
"""

try:
    cursor.execute(create_table_query)
    conn.commit()
    print("✅ Table 'users' created successfully.")
except mysql.connector.Error as err:
    print(f"❌ Error: {err}")
finally:
    cursor.close()
    conn.close()
