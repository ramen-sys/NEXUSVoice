import os
import psycopg2
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


load_dotenv()

mcp=FastMCP("db_server")

def get_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

@mcp.tool()
def query_staff(question_topic:str) -> str:
    "Looks up IT helpdesk staff information fromt the database, Use this information about who is on call, staff contact"
    "details,extensions, departments, or who to contact for a specific type of IT issue (network,hardware or software)"
    "question_topic should be a short keyword like network or on call or a staff members name"

    conn=get_connection()
    cursor=conn.cursor()
    words=question_topic.split()
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



