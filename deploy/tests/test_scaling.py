import urllib.request
import json
import time

print("Testing Load Balancer Distribution...\n")

container_counts = {}

for i in range(20):
    try:
        req = urllib.request.Request("http://localhost:8000/health")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            hostname = data.get("hostname", "unknown")
            print(f"Request {i+1:02d} -> Handled by Container: {hostname}")
            container_counts[hostname] = container_counts.get(hostname, 0) + 1
    except Exception as e:
        print(f"Request {i+1:02d} -> Failed: {e}")
    time.sleep(0.1)
    
print("\n--- Distribution Summary ---")
for hostname, count in container_counts.items():
    print(f"Container {hostname}: {count} requests")
print(f"Total Requests: {sum(container_counts.values())}")