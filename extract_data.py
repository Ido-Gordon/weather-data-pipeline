import os
import requests
import sqlite3
import time
from datetime import datetime

def run_weather_etl():
    # Direct API key string injection to completely bypass .env missing files
    API_KEY = os.environ.get('OPENWEATHER_API_KEY')
    CITIES = ['Tel Aviv', 'Jerusalem', 'Haifa', 'Beersheba', 'Eilat']
    all_weather_data = []

    print("\n--- Starting data extraction from server ---")

    # 1. Extract: Fetch live data from OpenWeatherMap API
    for city in CITIES:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                
                # Standard SQL compliant ISO string format
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                weather_record = (
                    data['name'],
                    data['main']['temp'],
                    data['main']['humidity'],
                    data['weather'][0]['description'],
                    current_time
                )
                all_weather_data.append(weather_record)
                print(f"Success: {city}")
            else:
                print(f"Error for city {city}: Status Code {response.status_code}")
        except Exception as e:
            print(f"Failed to connect for city {city}: {e}")

    # 2. Transform & Load: Bulk insert to SQLite database using pure SQL
    if all_weather_data:
        conn = sqlite3.connect('weather_history.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_weather (
                City TEXT,
                Temperature REAL,
                Humidity REAL,
                Description TEXT,
                Timestamp TEXT
            )
        """)
        
        cursor.executemany("""
            INSERT INTO daily_weather (City, Temperature, Humidity, Description, Timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, all_weather_data)
        
        conn.commit()
        
        # 3. Verification: Audit table transactions directly via cursor fetch
        print("\nData currently in the database (Last 5 records):")
        cursor.execute("SELECT * FROM daily_weather ORDER BY Timestamp DESC LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
            
        conn.close()
        print("\n--- Operation completed successfully! ---")
    else:
        print("\n--- No data was extracted in this cycle ---")

if __name__ == "__main__":
    while True:
        try:
            print("\nRunning automated data extraction cycle...")
            run_weather_etl()
            
            print("Success! Sleeping for 1 hour...")
            time.sleep(3600)
            
        except Exception as e:
            print(f"Critical error occurred in pipeline loop: {e}")
            time.sleep(60)