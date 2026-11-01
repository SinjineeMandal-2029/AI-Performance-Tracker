"""
Run the SQL files against your online database from your own computer.

Usage (Windows PowerShell example):
    pip install mysql-connector-python
    $env:DB_HOST="xxx.aivencloud.com"; $env:DB_PORT="12345"
    $env:DB_USER="avnadmin"; $env:DB_PASSWORD="your-password"; $env:DB_NAME="defaultdb"
    python init_db.py schema_cloud.sql
    python init_db.py demo_data.sql      # only after you signed up a student on the live site
"""
import os, sys
import mysql.connector

path = sys.argv[1] if len(sys.argv) > 1 else "schema_cloud.sql"

conn = mysql.connector.connect(
    host=os.environ["DB_HOST"],
    port=int(os.environ.get("DB_PORT", 3306)),
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    database=os.environ["DB_NAME"],
)
cur = conn.cursor()

lines = [l for l in open(path, encoding="utf-8").read().splitlines()
         if not l.strip().startswith("--")]
statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]

for i, stmt in enumerate(statements, 1):
    cur.execute(stmt)
    print(f"ok {i}/{len(statements)}")

conn.commit()
cur.close()
conn.close()
print("Done:", path)
