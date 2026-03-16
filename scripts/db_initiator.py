

import logging
import os
import sqlite3


LOG_FILE = "agent_interactions.log"
DB_PATH = "example.db"
# Configure logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("sql_agent")

logger = setup_logging()
def initialize_db():
    if not os.path.exists(DB_PATH):
        logger.info("Initializing new database with sample data")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE regions (
            region_id INTEGER PRIMARY KEY,
            region_name TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_name TEXT,
            amount REAL,
            region_id INTEGER,
            FOREIGN KEY (region_id) REFERENCES regions(region_id)
        )
        """)

        cursor.executemany("INSERT INTO regions VALUES (?, ?)",
                          [(1, 'North'), (2, 'South'), (3, 'East'), (4, 'West')])

        cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)",
                          [(1, 'Alice', 100.0, 1),
                           (2, 'Bob', 200.0, 2),
                           (3, 'Charlie', 150.0, 1),
                           (4, 'David', 300.0, 3),
                           (5, 'Eve', 250.0, 4)])

        conn.commit()
        conn.close()
        logger.info("Database initialization complete")

initialize_db()