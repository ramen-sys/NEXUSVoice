import os
import psycopg2 
from dotenv import load_dotenv

load_dotenv()

db_url=os.environ.get("DATABASE_URL")

if not db_url:
    print("Error: URL not found")

else:
    try:
        conn=psycopg2.connect(db_url)
        cursor=conn.cursor()

        cursor.execute("SELECT version()")
        result=cursor.fetchone()

        print("Connected Successfully")

        cursor.close()
        conn.close()

    except Exception as e:
        print("Connection failed: ",e)
