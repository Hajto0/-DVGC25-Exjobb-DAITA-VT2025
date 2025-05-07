import os
import argparse
from pathlib import Path
import csv

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

def process_server_folders(results_dir):
    results = {}

    base_path = Path(results_dir)
    for server in base_path.iterdir():
        if not server.is_dir():
            continue

        total_duration = 0
        total_size = 0

        # Process each url
        for url_folder_num in range(50):
            print(f"Processing URL#{url_folder_num} on {server}")

            url_folder = server / str(url_folder_num)
            if not url_folder.is_dir():
                continue

            total_log_duration = 0
            total_log_size = 0

            for log_file in url_folder.glob("*.log"):
                log_size, duration = process_log_file(log_file)
                total_log_size += log_size
                total_log_duration += duration

            log_size = total_log_size / 1024**2  # Convert to MiB
            log_duration = total_log_duration

            total_size += log_size
            total_duration += log_duration

        # Calculate average duration and bandwidth for the server
        average_duration = total_duration / 5000
        average_size = total_size / 5000

        results[server] = (average_duration, average_size)

    return results

def print_and_save_results(results, output_path=None):
    print("\n====================================== SUMMARY ======================================")
    print(f"{'Server name':<20} | {'Average Duration (s)':<22} | {'Average Bandwidth (MiB)':<25}")
    print("-" * 71)

    for server, (average_duration, average_size) in results.items():
        print(f"{server.name:<20} | {average_duration:<22.2f} | {average_size:<25.2f}")


    if output_path:
        with open(output_path, mode='w', newline='') as file:
            writer = csv.writer(file)

            header = [
            f"{'Server':<20}",
            f"{'Average Duration (s)':<22}",
            f"{'Average Bandwidth (MiB)':<22}"
            ]
            writer.writerow(header)

            for server_name, (average_duration, average_size) in results.items():
                writer.writerow([
                    f"{str(server_name.name):<20}",
                    f"{round(average_duration, 2):<22}",
                    f"{round(average_size, 2):<22}"
                ])
            print(f"\nSatistics saved to: {output_path}\n")
    else:
        print("Can't save, output file not defined\n")

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process log files and sum bytes transferred.")
    parser.add_argument("results_dir", type=str, help="Path to the results directory")
    parser.add_argument("output_file", type=str, help="Path to output CSV file")

    args = parser.parse_args()

    statistics = process_server_folders(args.results_dir)

    output_path = args.output_file
    if output_path and not output_path.lower().endswith(".csv"):
        output_path += ".csv"

    print_and_save_results(statistics, output_path)