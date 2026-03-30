"""
Latency Analysis Script
Reads latency_log.csv and prints statistics
"""
import csv
import statistics

latencies = []
with open("latency_log.csv", "r") as f:
    reader = csv.reader(f)
    for row in reader:
        if row:
            latencies.append(float(row[1]))

print(f"Samples:  {len(latencies)}")
print(f"Average:  {statistics.mean(latencies):.2f} ms")
print(f"Min:      {min(latencies):.2f} ms")
print(f"Max:      {max(latencies):.2f} ms")
print(f"Std Dev:  {statistics.stdev(latencies):.2f} ms")