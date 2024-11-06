import argparse
import json
import os.path
import tempfile

import requests

def upload(target_data, server):
    print(f"Uploading to server: {server}")
    for entry in target_data:
        program_file_path = entry.get("model", None)
        metrics_file_path = entry.get("additional_metrics", None)

        if program_file_path and metrics_file_path:
            # Prepare the files parameter with open files
            try:
                with open(program_file_path, 'rb') as program_file, open(metrics_file_path, 'rb') as metrics_file:
                    files = {
                        "program_file_path": program_file,
                        "metrics_file_path": metrics_file
                    }
                    # Send the POST request with files
                    response = requests.post(f"http://{server}/batch", files=files)

                    # Check the response status
                    if response.status_code == 200:
                        print(f"Successfully uploaded: {program_file_path} and {metrics_file_path}")
                    else:
                        print(f"Failed to upload: {response.status_code} - {response.text}")
            except FileNotFoundError as e:
                print(f"File error: {e}")
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
        else:
            print("Missing model or metrics information in entry.")
            print(program_file_path)
            print(metrics_file_path)



def main():
    parser = argparse.ArgumentParser(description="DRACONIS Command Line Tool")
    subparsers = parser.add_subparsers(dest="command")

    upload_parser = subparsers.add_parser("upload", help="Upload analyses to server")
    upload_parser.add_argument("--target", required=True, help="Path to JSON file containing analyses")
    upload_parser.add_argument("--server", default="localhost:8000", help="Server IP (defaults to localhost:8000)")

    args = parser.parse_args()

    if args.command == "upload":
        # Load and parse the JSON file specified in --target
        with open(args.target, 'r') as f:
            target_data = json.load(f)

        # Pass parsed data to upload function
        upload(target_data, args.server)


if __name__ == "__main__":
    main()