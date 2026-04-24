import sqlite3

def check_data():
    # Path to your sqlite file
    # db_path = "redarky.sqlite"
    db_path = "D:/SaaS/ListeningAIAgent/ListeningAgentAi/redarky/redarky.sqlite"
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query the table
        cursor.execute("SELECT * FROM scraped_results")
        rows = cursor.fetchall()
        
        if not rows:
            print("Successfully connected, but the table is empty. 🕸️")
        else:
            print(f"Found {len(rows)} rows in 'scraped_results':")
            print("-" * 50)
            for row in rows:
                print(row)
                
        conn.close()
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
        print("Tip: Make sure you've run the /scrape endpoint at least once!")

if __name__ == "__main__":
    check_data()