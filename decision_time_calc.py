import statistics

# Open the file and read the decision times
with open("decision_times.txt", "r") as f:
    # Read all lines, convert to floats
    decision_times = [float(line.strip()) for line in f]

# Calculate the average (mean) and standard deviation
if decision_times:  # Ensure there's at least one value in the file
    avg_time = sum(decision_times) / len(decision_times)  # Average calculation
    std_dev = statistics.stdev(decision_times)  # Standard deviation calculation

    print(f"Average Decision Time: {avg_time:.6f} seconds")
    print(f"Standard Deviation of Decision Time: {std_dev:.6f} seconds")
else:
    print("No decision times found.")
print("________________")
with open("decision_times_full.txt", "r") as f:
# Read all lines, convert to floats
    decision_times = [float(line.strip()) for line in f]

# Calculate the average (mean) and standard deviation
if decision_times:  # Ensure there's at least one value in the file
    avg_time = sum(decision_times) / len(decision_times)  # Average calculation
    std_dev = statistics.stdev(decision_times)  # Standard deviation calculation

    print(f"Average Decision Time: {avg_time:.6f} seconds")
    print(f"Standard Deviation of Decision Time: {std_dev:.6f} seconds")
else:
    print("No decision times found.")
    
print("_______________")
with open("decision_times_self.txt", "r") as f:
    # Read all lines, convert to floats
    decision_times = [float(line.strip()) for line in f]

# Calculate the average (mean) and standard deviation
if decision_times:  # Ensure there's at least one value in the file
    avg_time = sum(decision_times) / len(decision_times)  # Average calculation
    std_dev = statistics.stdev(decision_times)  # Standard deviation calculation

    print(f"Average Decision Time: {avg_time:.6f} seconds")
    print(f"Standard Deviation of Decision Time: {std_dev:.6f} seconds")
else:
    print("No decision times found.")