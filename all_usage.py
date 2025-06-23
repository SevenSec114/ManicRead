import sqlite3
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import mplcursors

# Database connection and query execution
conn = sqlite3.connect("/home/syam/.config/manictime/ManicTimeReports.db")
cursor = conn.cursor()

query = """
SELECT G.name, A.StartLocalTime, A.EndLocalTime
FROM Ar_Activity AS A
JOIN Ar_Group AS G ON A.GroupId = G.GroupId
WHERE A.StartLocalTime IS NOT NULL AND A.EndLocalTime IS NOT NULL
"""

cursor.execute(query)
rows = cursor.fetchall()

# Calculate total usage time per application
usage = defaultdict(float)

for name, start, end in rows:
    try:
        t1 = datetime.fromisoformat(start)
        t2 = datetime.fromisoformat(end)
        usage[name] += (t2 - t1).total_seconds() / 3600
    except:
        continue

# Sort applications by usage time and take the top 10
top_usage = sorted(usage.items(), key=lambda x: -x[1])[:10]
names = [item[0] for item in top_usage]
hours = [item[1] for item in top_usage]

# Print results
print("📊 应用使用时长排行榜（单位：小时）\n")
for name, hours_value in top_usage:
    print(f"{name:<35} => {round(hours_value, 2)} 小时")

# Plotting the vertical bar chart
plt.figure(figsize=(14, 8))
bars = plt.bar(names, hours, color='skyblue')
plt.xlabel('Applications')
plt.ylabel('Usage Time (hours)')
plt.title('Top 10 Application Usage Time')
plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for better readability
plt.tight_layout()

# Add tooltips to show exact values on hover
cursor = mplcursors.cursor(bars, hover=True)
@cursor.connect("add")
def on_add(sel):
    height = sel.artist[sel.index].get_height()
    sel.annotation.set(text=f"{round(height, 2)} hours")

plt.show()

conn.close()