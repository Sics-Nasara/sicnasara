import pandas as pd
import matplotlib.pyplot as plt
import psycopg2

# Database connection details
conn = psycopg2.connect(
    host="localhost",
    database="qos",
    user="qosuser",
    password="qospassword"
)

# Query to fetch data
query = """
SELECT timestamp, download_speed
FROM qos_data
"""

# Fetch the data into a pandas DataFrame
df = pd.read_sql(query, conn)

# Close the database connection
conn.close()

# Set the timestamp as the DataFrame index
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)

# Define the threshold
threshold = 3.0  # You can adjust this value based on your requirement

# Plot the data
plt.figure(figsize=(10, 6))
plt.plot(df.index, df['download_speed'], label='Download Speed', color='b', marker='o')
plt.axhline(y=threshold, color='r', linestyle='--', label=f'Threshold ({threshold} Mbps)')

# Adding labels and title
plt.title('Download Speed Over Time')
plt.xlabel('Time')
plt.ylabel('Download Speed (Mbps)')
plt.legend()

# Display the plot
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
