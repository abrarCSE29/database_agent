# import sqlite3
# import os
# import logging
# from langchain_community.utilities import SQLDatabase
# from src.config import DB_PATH

# logger = logging.getLogger("sql_agent")

# def initialize_db():
#     if not os.path.exists(DB_PATH):
#         logger.info("Initializing new database with sample data")
#         conn = sqlite3.connect(DB_PATH)
#         cursor = conn.cursor()

#         cursor.execute("""
#         CREATE TABLE regions (
#             region_id INTEGER PRIMARY KEY,
#             region_name TEXT NOT NULL
#         )
#         """)

#         cursor.execute("""
#         CREATE TABLE orders (
#             order_id INTEGER PRIMARY KEY,
#             customer_name TEXT,
#             amount REAL,
#             region_id INTEGER,
#             FOREIGN KEY (region_id) REFERENCES regions(region_id)
#         )
#         """)

#         cursor.executemany("INSERT INTO regions VALUES (?, ?)",
#                           [(1, 'North'), (2, 'South'), (3, 'East'), (4, 'West')])

#         cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)",
#                           [(1, 'Alice', 100.0, 1),
#                            (2, 'Bob', 200.0, 2),
#                            (3, 'Charlie', 150.0, 1),
#                            (4, 'David', 300.0, 3),
#                            (5, 'Eve', 250.0, 4)])

#         conn.commit()
#         conn.close()
#         logger.info("Database initialization complete")

# def get_db_connection():
#     return sqlite3.connect(DB_PATH)

# # Database connection for LangChain
# db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")



# db = SQLDatabase.from_uri("mysql+mysqldb://scott:tiger@hostname/dbname")


import os
from urllib.parse import quote_plus
import logging
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
import pymysql  # If using mysqlclient, or import pymysql

load_dotenv()
logger = logging.getLogger("sql_agent")

# Construct the URI from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")
safe_password = quote_plus(DB_PASSWORD)
# SQLAlchemy URI format: mysql+mysqldb://user:password@host:port/dbname
MYSQL_URI = f"mysql+pymysql://{DB_USER}:{safe_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def initialize_db():
    """Initializes MySQL tables if they don't exist."""
    try:
        # Connect using the driver directly for DDL operations
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=int(DB_PORT)
        )
        cursor = conn.cursor()

        # MySQL uses 'IF NOT EXISTS' instead of checking os.path
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            region_id INT PRIMARY KEY,
            region_name VARCHAR(255) NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INT PRIMARY KEY,
            customer_name VARCHAR(255),
            amount FLOAT,
            region_id INT,
            FOREIGN KEY (region_id) REFERENCES regions(region_id)
        )
        """)

        # Checking if data exists before inserting to avoid duplicate errors
        cursor.execute("SELECT COUNT(*) FROM regions")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO regions (region_id, region_name) VALUES (%s, %s)",
                              [(1, 'North'), (2, 'South'), (3, 'East'), (4, 'West')])
            
            cursor.executemany("INSERT INTO orders (order_id, customer_name, amount, region_id) VALUES (%s, %s, %s, %s)",
                              [(1, 'Alice', 100.0, 1), (2, 'Bob', 200.0, 2)])
            
            conn.commit()
            logger.info("Database initialization complete")
        
        conn.close()
    except Exception as e:
        logger.error(f"Error initializing MySQL: {e}")
def get_db_connection():
    conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=int(DB_PORT)
        )
    return conn

db = SQLDatabase.from_uri(MYSQL_URI)