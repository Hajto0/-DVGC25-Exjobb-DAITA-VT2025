import os
import argparse
from pathlib import Path
import csv
import subprocess

def process_log_file(log_file):
    """Process each log file to calculate its total size and duration."""
    duration = 0
    total_log_size = 0
    sent_bandwidth = 0
    received_bandwidth = 0

    with open(log_file, "r") as f:
        for line in f:
            parts = line.strip().split(",")

            time, direction, size = parts
            size = int(size)

            if direction == 's':
                sent_bandwidth += size
            else:
                received_bandwidth += size

            duration = float(time) / (10 ** 9)  # Convert time to seconds (assuming nanoseconds)
            total_log_size += size

    return total_log_size, sent_bandwidth, received_bandwidth, duration

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
        

        print(f"Calculating metrics for {server.name}\n")

        total_duration = 0
        total_size = 0
        total_sent_bandwidth = 0
        total_received_bandwidth = 0

        for url_folder_num in range(50):
            print(f"Processing {server.name} URL#{url_folder_num}")  #DEBUG

            url_folder = server / str(url_folder_num)
            if not url_folder.is_dir():
                continue

            total_log_duration = 0
            total_log_size = 0
            total_log_sent_bandwidth = 0
            total_log_received_bandwidth = 0

            # Process log files (from 0.log to 99.log)
            for log_file in url_folder.glob("*.log"):
                log_size, sent_bandwidth, received_bandwidth, duration = process_log_file(log_file)
                total_log_size += log_size
                total_log_duration += duration
                total_log_sent_bandwidth += sent_bandwidth
                total_log_received_bandwidth += received_bandwidth

            # Calculate averages for the URL (5 devices * 20 samples = 100)
            average_log_size = (total_log_size / 100) / 1024**2  # Convert to MiB 
            average_log_sent_bandwidth = total_log_sent_bandwidth / 100 / 1024**2
            average_log_received_bandwidth = total_log_received_bandwidth / 100 / 1024**2
            average_log_duration = total_log_duration / 100

            total_size += average_log_size
            total_duration += average_log_duration
            total_sent_bandwidth += average_log_sent_bandwidth
            total_received_bandwidth += average_log_received_bandwidth

        # Calculate averages for the server
        average_duration = total_duration / 50
        average_size = total_size / 50
        average_sent_bandwidth = total_sent_bandwidth / 50
        average_received_bandwidth = total_received_bandwidth / 50

        #results[server] = (average_duration, average_size, average_sent_bandwidth, average_received_bandwidth, float(df_accuracy), float(rf_accuracy))
        results[server] = (average_duration, average_size, average_sent_bandwidth, average_received_bandwidth, 0, 0)

    return results

def print_and_save_results(results, output_path=None):
    print("\n===== SUMMARY =====")
    print(f"{'Server name':<25} | {'Defense':<20} | {'Average Duration (s)':<22} | {'Average Bandwidth (MiB)':<25} | {'Average Sent Bandwidth (MiB)':<30} | {'Average Received Bandwidth (MiB)':<30} | {'DF Accuracy':<12} | {'RF Accuracy':<12}")
    print("-" * 198)

    for server, (average_duration, average_size, average_sent_bandwidth, average_received_bandwidth, df_accuracy, rf_accuracy) in results.items():
        display_server_name, defense = is_server_defended(server.name)
        print(f"{display_server_name:<25} | {defense:<20} | {average_duration:<22.2f} | {average_size:<25.2f} | {average_sent_bandwidth:<30.2f} | {average_received_bandwidth:<32.2f} | {df_accuracy:<12} | {rf_accuracy:<12}")


    if output_path:
        with open(output_path, mode='w', newline='') as file:
            writer = csv.writer(file)

            header = [
            f"{'Server'}",
            f"{'Defense'}",
            f"{'Average Duration (s)'}",
            f"{'Average Bandwidth (MiB)'}",
            f"{'Average Sent Bandwidth (MiB)'}",
            f"{'Average Received Bandwidth (MiB)'}",
            f"{'DF Accuracy'}",
            f"{'RF Accuracy'}"
            ]
            writer.writerow(header)



            # Write each server's data with formatted output for better alignment
            for server_name, (average_duration, average_size, average_sent_bandwidth, average_received_bandwidth, df_accuracy, rf_accuracy) in results.items():
                display_server_name, defense = is_server_defended(server_name.name)
                writer.writerow([
                    f"{display_server_name}",
                    f"{defense}",
                    f"{round(average_duration, 2)}",
                    f"{round(average_size, 2)}",
                    f"{round(average_sent_bandwidth, 2)}",
                    f"{round(average_received_bandwidth, 2)}",
                    f"{round(df_accuracy, 2)}",
                    f"{round(rf_accuracy, 2)}"
                ])
            print(f"\nSatistics saved to: {output_path}\n")
    else:
        print("Can't save, output file not defined\n")

    return

def is_server_defended(text):
    if text.endswith("-ND"):
        return text[:-3], "Undefended"
    elif text.endswith(" DAITA OFF"):
        return text[:-10], "Undefended"
    elif text.endswith("-DT"):
        return text[:-3], "Daita"
    elif text.endswith(" DAITA ON"):
        return text[:-9], "Daita"
    else:
        return text, "unknown"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process log files, sum bytes transferred and runs Wf-attacks.")
    parser.add_argument("input_file", type=str, help="Path to the input directory")
    parser.add_argument("output_file", type=str, help="Path to output CSV file")

    args = parser.parse_args()

    statistics = process_server_folders(args.input_file)

    output_path = args.output_file
    if output_path and not output_path.lower().endswith(".csv"):
        output_path += ".csv"

    print_and_save_results(statistics, output_path)