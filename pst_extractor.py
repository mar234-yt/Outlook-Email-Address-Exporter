#!/usr/bin/env python3
import subprocess
import re
import csv
import sys
import os
import tempfile
import shutil


def extract_with_readpst(pst_path, output_csv):
    """Extract using readpst command line tool."""
    if not os.path.exists(pst_path):
        print(f"Error: File not found: {pst_path}")
        sys.exit(1)

    temp_dir = tempfile.mkdtemp(prefix='pst_extract_')

    try:
        print(f"Extracting PST to temporary directory...")
        result = subprocess.run(
            ['readpst', '-M', '-o', temp_dir, pst_path],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"readpst error: {result.stderr}")
            sys.exit(1)

        addresses = set()
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'

        print(f"Scanning extracted emails...")
        count = 0

        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', errors='ignore') as f:
                        content = f.read()
                        found = re.findall(email_pattern, content)
                        for addr in found:
                            if len(addr) > 5 and '.' in addr.split('@')[-1]:
                                addresses.add(addr.lower())
                    count += 1
                    if count % 1000 == 0:
                        print(f"  Processed {count} files...")
                except Exception as e:
                    continue

        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['email_address'])
            for addr in sorted(addresses):
                writer.writerow([addr])

        print(f"\nDone! Found {len(addresses)} unique addresses")
        print(f"Output saved to: {output_csv}")
        print(f"Full path: {os.path.abspath(output_csv)}")

    except FileNotFoundError:
        print("ERROR: 'readpst' command not found.")
        sys.exit(1)
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 pst_extractor.py <input.pst> <output.csv>")
        sys.exit(1)

    extract_with_readpst(sys.argv[1], sys.argv[2])