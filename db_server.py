import os
import psycopg2
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import time


load_dotenv()

mcp=FastMCP("db_server")

def get_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

@mcp.tool()
def query_staff(question_topic:str) -> str:
    """Looks up IT helpdesk staff information from the database — ONLY for
    questions about who is on call, staff contact details, extensions,
    departments, or who to contact for an IT issue (network, hardware, software).

    DO NOT use this tool for: general knowledge questions (capitals, geography,
    history, etc.), current events, weather, or any topic unrelated to your
    own company's IT staff.

    question_topic should be a short keyword like 'network', 'on-call', or a
    staff member's name — never a full unrelated question."""
    
    for attempt in range(2):
        try:

            conn=get_connection()
            cursor=conn.cursor()
            list_all_keywords = ["all staff", "everyone", "all members", "full list", "list all"]
            if any(kw in question_topic.lower() for kw in list_all_keywords):
                cursor.execute("SELECT id, name, role, department, on_call_day, extension, specialty FROM staff")
                all_rows = cursor.fetchall()
                cursor.close()
                conn.close()
                if not all_rows:
                    return "NO_RESULTS"
                formatted = []
                for row in all_rows:
                    _, name, role, department, on_call_day, extension, specialty = row
                    formatted.append(
                        f"{name} ({role}, {department}) - "
                        f"On call: {on_call_day or 'not on rotation'}, "
                        f"Ext: {extension}, Specialty: {specialty or 'N/A'}"
                    )
                return "\n".join(formatted)
            on_call_keywords = ["on call", "on-call", "oncall", "who is on call", "on call today", "on call this week"]
            if any(kw in question_topic.lower() for kw in on_call_keywords):
                cursor.execute(
                    "SELECT id, name, role, department, on_call_day, extension, specialty "
                    "FROM staff WHERE on_call_day IS NOT NULL"
                )
                all_rows = cursor.fetchall()
                cursor.close()
                conn.close()
                if not all_rows:
                    return "NO_RESULTS"
                formatted = []
                for row in all_rows:
                    _, name, role, department, on_call_day, extension, specialty = row
                    formatted.append(
                        f"{name} ({role}, {department}) - "
                        f"On call: {on_call_day}, Ext: {extension}, Specialty: {specialty or 'N/A'}"
                    )
                return "\n".join(formatted)
   
            words = [w for w in question_topic.split() if len(w) >= 3]
            all_rows=[]
            seen_ids=set()
            for word in words:

                cursor.execute(
                    """ SELECT id,name,role,department, on_call_day,extension,specialty
                    FROM staff
                    WHERE name ILIKE %s 
                    OR specialty ILIKE %s
                    OR department ILIKE %s 
                    OR on_call_day ILIKE %s""",
                    (f'%{word}%',f"%{word}%",f"%{word}%", f"%{word}%")

                    
                )
                for row in cursor.fetchall():
                    row_id=row[0]
                    if row_id not in seen_ids:
                        seen_ids.add(row_id)
                        all_rows.append(row)
        
            cursor.close()
            conn.close()
            break
        except psycopg2.OperationalError as e:
            if attempt == 0:
                print(f"[DB connection dropped, retrying... {e}]")
                time.sleep(1)
                continue
            else:
                return f"DB_ERROR: {e}"

    if not all_rows:
        return "NO_RESULTS"
    

    formatted=[]
    for row in all_rows:
        _,name, role, department, on_call_day, extension, specialty = row
        formatted.append(
            f"{name} ({role}, {department}) - "
            f"On call: {on_call_day or 'not on rotation'}, "
            f"Ext: {extension}, Specialty: {specialty or 'N/A'}"
        )

    return "\n".join(formatted)

if __name__=="__main__":
    mcp.run()



