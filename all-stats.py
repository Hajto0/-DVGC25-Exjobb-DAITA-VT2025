import os
import argparse
from pathlib import Path
import csv
import subprocess

def process_log_file(log_file):
    """Process each log file to calculate its total size and duration."""
    duration = 0
    log_size = 0

    with open(log_file, "r") as f:
        for line in f:
            parts = line.strip().split(",")

            time, direction, size = parts
            size = int(size)

            duration = float(time) / (10 ** 9)  # Convert time to seconds (assuming nanoseconds)
            log_size += size

    return log_size, duration

def process_server_folders(input_file):
    results = {}

    base_path = Path(input_file)
    for server in sorted(base_path.iterdir()):
        if not server.is_dir() or server.name.startswith("."):
            continue
        
        try:
            print(f"Calculating DF accuracy on {server.name}\n")
            result = subprocess.run(
                    ["python3", "df.py", "-d", server, "-c", "50", "-s", "100", "--epochs", "30", "--seed", "0", "--train", "-l"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
            df_accuracy = result.stdout.strip().split("\n")[-1]
            print(f"{server.name:<35} {df_accuracy}\n") #DEBUG
        except Exception as e:
            print(f"{server.name:<35} ERROR: {e}")

        try:
            print(f"Calculating RF accuracy on {server.name}\n")
            result = subprocess.run(
                    ["python3", "rf.py", "-d", server, "-c", "50", "-s", "100", "--epochs", "30", "--seed", "0", "--train"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
            rf_accuracy = result.stdout.strip().split("\n")[-1]
            print(f"{server.name:<35} {rf_accuracy}\n") #DEBUG
        except Exception as e:
            print(f"{server.name:<35} ERROR: {e}")

        total_duration = 0
        total_size = 0

        print(f"Calculating metrics for {server.name}\n")

        for url_folder_num in range(50):
            #print(f"Processing URL#{url_folder_num} on {server}")  #DEBUG

            url_folder = server / str(url_folder_num)
            if not url_folder.is_dir():
                continue

            total_log_duration = 0
            total_log_size = 0

            # Process log files (from 0.log to 99.log)
            for log_file in url_folder.glob("*.log"):
                log_size, duration = process_log_file(log_file)
                total_log_size += log_size
                total_log_duration += duration

            # Calculate average log size and duration for this URL
            average_log_size = (total_log_size / 100) / 1024**2  # Convert to MiB
            average_log_duration = total_log_duration / 100

            total_size += average_log_size
            total_duration += average_log_duration

        # Calculate average duration and bandwidth for the server
        average_duration = total_duration / 50
        average_size = total_size / 50

        results[server] = (average_duration, average_size, float(df_accuracy), float(rf_accuracy))

    return results

def print_and_save_results(results, output_path=None):
    print("\n===== SUMMARY =====")
    print(f"{'Server name':<25} | {'Average Duration (s)':<22} | {'Average Bandwidth (MiB)':<25} | {'DF Accuracy':<12} | {'RF Accuracy':<12}")
    print("-" * 71)

    for server, (average_duration, average_size, df_accuracy, rf_accuracy) in results.items():
        print(f"{server.name:<25} | {average_duration:<22.2f} | {average_size:<25.2f} | {df_accuracy:<12} | {rf_accuracy:<12}")


    if output_path:
        with open(output_path, mode='w', newline='') as file:
            writer = csv.writer(file)

            header = [
            f"{'Server':<25}",
            f"{'Average Duration (s)':<22}",
            f"{'Average Bandwidth (MiB)':<22}",
            f"{'DF Accuracy':<12}",
            f"{'RF Accuracy':<12}"
            ]
            writer.writerow(header)

            # Write each server's data with formatted output for better alignment
            for server_name, (average_duration, average_size, df_accuracy, rf_accuracy) in results.items():
                writer.writerow([
                    f"{str(server_name.name):<20}",
                    f"{round(average_duration, 2):<22}",
                    f"{round(average_size, 2):<22}",
                    f"{round(df_accuracy, 2):<22}",
                    f"{round(rf_accuracy, 2):<12}"
                ])
            print(f"\nSatistics saved to: {output_path}\n")
    else:
        print("Can't save, output file not defined\n")

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process log files and sum bytes transferred.")
    parser.add_argument("input_file", type=str, help="Path to the input directory")
    parser.add_argument("output_file", type=str, help="Path to output CSV file")

    args = parser.parse_args()

    statistics = process_server_folders(args.input_file)

    output_path = args.output_file
    if output_path and not output_path.lower().endswith(".csv"):
        output_path += ".csv"

    print_and_save_results(statistics, output_path)