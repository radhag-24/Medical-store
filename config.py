import json
import mysql.connector
import os

def get_db_connection():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    
    with open(config_path) as f:
        config = json.load(f)
    
    conn = mysql.connector.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )
    return conn
