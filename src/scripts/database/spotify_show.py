import psycopg2
from datetime import datetime, timedelta
import pytz
import kewi

# Replace with your actual database connection string
ARG_time_span : kewi.args.TimeSpan = "last 4 hours"
kewi.args.init()

print(ARG_time_span)

# Connect to the PostgreSQL database
try:
    connection = psycopg2.connect(kewi.globals.Dillerbase.CONNECTION_STRING)
    cursor = connection.cursor()

    # Get the local timezone
    local_tz = pytz.timezone(kewi.globals.TIMEZONE)  # like 'America/Los_Angeles'

    # SQL query to fetch recent song_listens events
    query = """
        SELECT sl.timestamp, s.name, s.duration_ms
        FROM song_listens sl
        JOIN songs s ON sl.song_id = s.id
        WHERE sl.timestamp >= %s
        AND sl.timestamp <= %s
        ORDER BY sl.timestamp DESC;
    """
    cursor.execute(query, (ARG_time_span.start, ARG_time_span.end,))
    results = cursor.fetchall()


    lines = []
    # Print the results in the desired format
    for timestamp, song_name, duration_ms in results:
        timestamp: datetime
        
        iso_timestamp = timestamp.isoformat()
        local_time = timestamp.replace(tzinfo=pytz.utc).astimezone(local_tz)
        formatted_date = local_time.strftime("%b %d")
        formatted_time = local_time.strftime("%I:%M %p")
        if formatted_time.startswith("0"):
            formatted_time = " " + formatted_time[1:]
        formatted_date += ", " + formatted_time
        
        seconds_component = local_time.second / 100  # Get the seconds as a decimal
        duration_formatted = str(timedelta(milliseconds=duration_ms)).split(':')[-2:]  # Get the minutes and seconds
        formatted_duration = ":".join(duration_formatted)

        lines.append(f"{formatted_date} ({seconds_component:.2f})   |   \"{song_name}\"   | ({formatted_duration}) {{{timestamp}}}")
    lines.reverse()
    for line in lines:
        print(line)

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if connection:
        cursor.close()
        connection.close()

