import argparse
import os
import multiprocessing
from scapy.all import PcapReader
from datetime import datetime
import math
from pathlib import Path
import requests
import sys
#from tqdm import tqdm

def main(args):
    print(f"Results folder: {args.results}")

    if os.path.exists(args.results):
        print(f"Error: The results folder {args.results} already exists.\n")
        return
                
    if not check_dataset_structure(Path(args.dir)):
        print("Input directory file structure not valid\n")
        return
    
    tasks = []

    with multiprocessing.Pool() as pool:
        for server in Path(args.dir).iterdir():
            if server.is_dir():
                for url_id in range(1, 51):  # URL 1–50
                    count = 0
                    for sample_id in range(1, 21):  # Sample 1–20
                        for device_id in range(1, 6):  # Enhet 1–5
                            # Input PCAP-fil
                            pcap_path = server / f"URL_{url_id}_Sample_{sample_id}_D_{device_id}.pcap"
                            
                            # Output-struktur: results/[Server]/[URL]/[Sample].log
                            log_dir = os.path.join(
                                args.results,
                                server.name,
                                f"{url_id-1}"  # Använd URL-id för att skapa undermappen
                            )
                            os.makedirs(log_dir, exist_ok=True)
                            
                            log_path = os.path.join(log_dir, f"{count}.log")
                            
                            if os.path.exists(log_path):
                                print(f"{server}/URL {url_id}/Sample {sample_id}/ Device{device_id} Log file already exists\n")
                            else:
                                tasks.append(
                                    pool.apply_async(
                                        parse_pcap,
                                        args=(str(pcap_path), log_path, False)
                                    )
                                )
                            count += 1

        #for task in tqdm(tasks, desc="Processing tasks", unit="task"):
            #task.get()
        total = len(tasks)
        for i, task in enumerate(tasks, start=1):
            task.get()
            progress = (i / total) * 100
            sys.stdout.write(f"\rProgress: {i}/{total} ({progress:.1f}%)")
            sys.stdout.flush()
        
    print("\nParse complete!\n")
    return


def check_dataset_structure(input_file_path):
    print(f"Checking dataset structure in {input_file_path}...")
    
    for folder in input_file_path.iterdir():
        if folder.is_dir():
            for url_id in range(1, 51):
                for sample_id in range(1, 21):
                    for device_id in range(1, 6):
                        pcap = folder / f"URL_{url_id}_Sample_{sample_id}_D_{device_id}.pcap"
                        png = folder / f"URL_{url_id}_Sample_{sample_id}_D_{device_id}.png"
                        if not pcap.exists():
                            print(f"Error: {pcap} is missing")
                            return False
                        if not png.exists():
                            print(f"Error: {png} is missing")
                            return False
    print("Dataset structure is ok.")
    return True

def parse_pcap(pcap_file, trace_file, server_name):
    #print(f"parse {pcap_file} to {trace_file}")    #DEBUG
    first_timestamp = None
    lines = []

    try:
        capture = PcapReader(str(pcap_file))
        for packet in capture:
            if first_timestamp is None and packet.time:
                first_timestamp = datetime.fromtimestamp(float(packet.time))
            
            parsed_packet = parse_packet(packet, first_timestamp, server_name)
            if parsed_packet:  # Check if packet was successfully parsed
                lines.append(parsed_packet)
    except Exception as e:
        print(f"Error processing pcap file: {e}")

    with open(trace_file, "w") as f:
        f.write("\n".join(lines))

def parse_packet(packet, first_timestamp, server_name):
    global vpn_dict
    def compare_IP(packet):
        return packet['IP'].src != vpn_dict.get(server_name, False) or packet['IP'].dst != vpn_dict.get(server_name, False)

    # Check if packet has IP layer and the required attributes
    if packet.haslayer('IP') and hasattr(packet, 'time') and first_timestamp:
        if server_name:
            if compare_IP(packet): return None
        src_ip = packet['IP'].src
        dir = "s" if src_ip.startswith("192.168") else "r"
        timestamp = datetime.fromtimestamp(float(packet.time))
        duration = timestamp - first_timestamp
        timestamp = max(0, duration.total_seconds() * 1000 * 1000 * 1000)   # Convert to nanoseconds, but make sure it's not negative

        return f"{timestamp:.0f},{dir},{packet['IP'].len}"
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check dataset.")
    parser.add_argument("--dir", required=True, help="root folder")
    parser.add_argument("--results", required=True, help="results folder")
    parser.add_argument("--classes", default=50, type=int, help="number of classes")
    parser.add_argument("--samples", default=100, type=int, help="number of samples")

    main(parser.parse_args())