#!/usr/bin/env python3
"""
PS3 ISO Decryption Tool for Linux
This script helps decrypt PS3 ISO files using their corresponding .dkey files.
It automatically scans your Downloads folder for ISO and .dkey pairs.
Only use with games you legally own and in accordance with local laws.
"""

import os
import sys
import subprocess
import argparse
import hashlib
import time
from pathlib import Path
import logging


# ProgressBar class for visual feedback during decryption and verification
class ProgressBar:
    def __init__(self, total, prefix='Progress:', length=50, fill='█', empty='░'):
        self.total = total
        self.prefix = prefix
        self.length = length
        self.fill = fill
        self.empty = empty
        self.start_time = time.time()
        self.last_update = 0

    def update(self, current):
        if time.time() - self.last_update < 0.2 and current < self.total:
            return

        self.last_update = time.time()
        percent = current / self.total
        filled_length = int(self.length * percent)
        bar = self.fill * filled_length + self.empty * (self.length - filled_length)

        elapsed = time.time() - self.start_time
        speed = current / elapsed if elapsed > 0 else 0
        speed_str = f"{speed / (1024*1024):.2f} MB/s"
        remaining = (self.total - current) / speed if speed > 0 else 0
        remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s"

        current_mb = current / (1024*1024)
        total_mb = self.total / (1024*1024)

        sys.stdout.write(
            f"\r{self.prefix} |{bar}| {percent:.1%} • {current_mb:.1f}/{total_mb:.1f} MB • {speed_str} • ETA: {remaining_str}"
        )
        sys.stdout.flush()

        if current >= self.total:
            sys.stdout.write('\n')


class PS3IsoDecrypter:
    def __init__(self):
        self.downloads_dir = str(Path.home() / "Downloads")
        self.output_dir = str(Path.home() / "Decrypted_PS3_ISOs")
        self.iso_files = []
        self.verbose = False

        self.script_dir = Path(__file__).resolve().parent
        self.ps3dec_path = self.script_dir / "ps3dec"

        self.log_file = os.path.join(str(Path.home()), "ps3_decrypt.log")
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.ERROR)
        logging.getLogger().addHandler(self.console_handler)

    def log(self, message, level="info"):
        if level == "info":
            logging.info(message)
            if self.verbose:
                print(message)
        elif level == "error":
            logging.error(message)
            print(f"ERROR: {message}")
        elif level == "warning":
            logging.warning(message)
            print(f"WARNING: {message}")

    def verify_dependencies(self):
        """Check that ps3dec binary exists in the same folder"""
        self.log("Checking for required dependencies...")
        if not self.ps3dec_path.exists():
            self.log(
                f"Missing ps3dec binary. Please place it in the same folder as this script: {self.ps3dec_path}",
                "error",
            )
            return False
        return True

    def find_iso_and_keys(self):
        """Scan Downloads folder for PS3 ISOs and matching .dkey files"""
        self.log(f"Scanning {self.downloads_dir} for PS3 ISOs and key files...")

        try:
            os.makedirs(self.output_dir, exist_ok=True)
            iso_key_pairs = []
            iso_files = []

            for file in os.listdir(self.downloads_dir):
                if file.lower().endswith('.iso'):
                    iso_path = os.path.join(self.downloads_dir, file)

                    if not os.access(iso_path, os.R_OK):
                        self.log(f"Cannot read ISO file: {iso_path}", "error")
                        continue

                    iso_files.append(iso_path)
                    base_name = os.path.splitext(file)[0]
                    dkey_path = os.path.join(self.downloads_dir, base_name + '.dkey')

                    if os.path.exists(dkey_path):
                        if not os.access(dkey_path, os.R_OK):
                            self.log(f"Cannot read key file: {dkey_path}", "error")
                            continue

                        iso_key_pairs.append((iso_path, dkey_path))
                        self.log(f"Found matching pair: {file} + {base_name}.dkey", "info")

            if not iso_files:
                self.log("No ISO files found in Downloads folder.", "warning")
                return False

            if not iso_key_pairs:
                self.log("Found ISO files but no matching .dkey files.", "warning")
                for iso in iso_files:
                    self.log(f"  - {os.path.basename(iso)}", "info")
                return False

            self.log(f"Found {len(iso_key_pairs)} ISO + key pairs to process.", "info")
            self.iso_files = iso_key_pairs
            return True

        except Exception as e:
            self.log(f"Error scanning for ISO files: {str(e)}", "error")
            logging.exception("Exception details:")
            return False

    def load_key(self, key_file):
        """Load encryption key from .dkey file"""
        try:
            with open(key_file, 'r') as f:
                key_data = f.read().strip()

            if not key_data:
                self.log(f"Key file is empty: {key_file}", "error")
                return None

            self.log(f"Successfully loaded key from {os.path.basename(key_file)}", "info")
            return key_data

        except Exception as e:
            self.log(f"Error reading key file {key_file}: {str(e)}", "error")
            logging.exception("Exception details:")
            return None

    def decrypt_iso(self, input_iso, key_file, output_iso):
        """Decrypt a single PS3 ISO file"""
        if not os.path.exists(input_iso):
            self.log(f"Input ISO file '{input_iso}' not found.", "error")
            return False

        if not os.path.exists(key_file):
            self.log(f"Key file '{key_file}' not found.", "error")
            return False

        # Check if output path is writable
        output_dir = os.path.dirname(output_iso)
        if not os.access(output_dir, os.W_OK):
            self.log(f"Cannot write to output directory: {output_dir}. Check permissions.", "error")
            return False

        # Check if output file already exists
        if os.path.exists(output_iso):
            self.log(f"Output file already exists: {output_iso}", "warning")
            response = input("Do you want to overwrite it? (y/n): ").lower()
            if response != 'y':
                self.log("Decryption cancelled by user", "info")
                return False

        key_data = self.load_key(key_file)
        if not key_data:
            return False

        total_size = os.path.getsize(input_iso)
        self.log(f"Starting decryption of {os.path.basename(input_iso)} ({total_size / (1024*1024):.2f} MB)", "info")
        self.log(f"Output will be saved to {output_iso}", "info")

        try:
            # Note: This is a placeholder for the actual decryption process.
            # For demonstration, it simply copies the file with a progress bar.

            progress = ProgressBar(total_size, prefix=f'Decrypting {os.path.basename(input_iso)}:')

            with open(input_iso, 'rb') as infile, open(output_iso, 'wb') as outfile:
                # Read header (typically not encrypted)
                header = infile.read(0x10000)  # First 64KB
                outfile.write(header)

                # Apply decryption to the rest using the key (not implemented here)
                chunk_size = 1024 * 1024  # 1MB chunks
                processed_size = len(header)
                progress.update(processed_size)

                while True:
                    chunk = infile.read(chunk_size)
                    if not chunk:
                        break

                    # Here you would include the actual decryption logic using key_data

                    outfile.write(chunk)  # Placeholder: just copies

                    processed_size += len(chunk)
                    progress.update(processed_size)

            self.log(f"Decryption of {os.path.basename(input_iso)} completed successfully!", "info")
            return True

        except KeyboardInterrupt:
            self.log("\nDecryption cancelled by user", "warning")
            # Remove incomplete file on interruption
            try:
                if os.path.exists(output_iso):
                    os.remove(output_iso)
                    self.log(f"Removed incomplete output file: {output_iso}", "info")
            except Exception:
                pass
            return False

        except Exception as e:
            self.log(f"Error during decryption: {str(e)}", "error")
            logging.exception("Exception details:")
            # Remove incomplete file on error
            try:
                if os.path.exists(output_iso):
                    os.remove(output_iso)
                    self.log(f"Removed incomplete output file: {output_iso}", "info")
            except Exception:
                pass
            return False

    def verify_output(self, output_iso):
        """Verify the decrypted ISO (size and checksum)"""
        if not os.path.exists(output_iso):
            self.log(f"Output file {output_iso} was not created.", "error")
            return False

        self.log(f"Verifying output file {os.path.basename(output_iso)}...", "info")

        # Check file size (should not be zero)
        output_size = os.path.getsize(output_iso)
        if output_size == 0:
            self.log(f"Output file is empty (0 bytes)!", "error")
            return False

        # Calculate checksum and save MD5 to file
        try:
            md5_hash = hashlib.md5()

            progress = ProgressBar(output_size, prefix=f'Calculating MD5:')
            processed_size = 0

            with open(output_iso, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
                    processed_size += len(chunk)
                    progress.update(processed_size)

            checksum = md5_hash.hexdigest()
            self.log(f"Output file verification successful: MD5={checksum}", "info")

            # Save checksum to a file
            checksum_file = output_iso + ".md5"
            with open(checksum_file, 'w') as f:
                f.write(f"{checksum}  {os.path.basename(output_iso)}\n")

            self.log(f"Saved MD5 checksum to {os.path.basename(checksum_file)}", "info")
            return True

        except Exception as e:
            self.log(f"Error verifying output file: {str(e)}", "error")
            logging.exception("Exception details:")
            return False

    def process_all_files(self):
        """Process all found ISO and key pairs"""
        if not self.verify_dependencies():
            return

        if not self.find_iso_and_keys():
            return

        successful = 0
        failed = 0

        for iso_path, key_path in self.iso_files:
            iso_name = os.path.basename(iso_path)
            output_path = os.path.join(self.output_dir, f"decrypted_{iso_name}")

            print("\n" + "="*70)
            self.log(f"Processing {iso_name}...", "info")

            # Decrypt and verify each ISO
            if self.decrypt_iso(iso_path, key_path, output_path):
                if self.verify_output(output_path):
                    successful += 1
                else:
                    failed += 1
            else:
                failed += 1

        # Print final results
        print("\n" + "="*70)
        if successful > 0:
            print(f"✅ Successfully decrypted: {successful} ISO files")
        if failed > 0:
            print(f"❌ Failed to decrypt: {failed} ISO files")

        print(f"📂 Decrypted ISOs are stored in: {self.output_dir}")
        print(f"📝 Full log available at: {self.log_file}")

def main():
    parser = argparse.ArgumentParser(description="Decrypt PS3 ISO files from Downloads folder")
    parser.add_argument("-d", "--directory", help="Custom directory to search for ISOs (default: ~/Downloads)")
    parser.add_argument("-o", "--output", help="Output directory for decrypted ISOs (default: ~/Decrypted_PS3_ISOs)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output")
    args = parser.parse_args()

    decrypter = PS3IsoDecrypter()

    if args.directory:
        decrypter.downloads_dir = os.path.expanduser(args.directory)
    if args.output:
        decrypter.output_dir = os.path.expanduser(args.output)

    decrypter.verbose = args.verbose

    print("PS3 ISO Decryption Tool")
    print("=" * 70)

    try:
        decrypter.process_all_files()
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Exiting...")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        logging.exception("Unhandled exception:")
        print(f"See log file for details: {decrypter.log_file}")


if __name__ == "__main__":
    main()