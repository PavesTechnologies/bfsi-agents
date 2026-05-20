import os

def combine_env_files(target_dir=".", output_filename="all.env"):
    output_path = os.path.abspath(os.path.join(target_dir, output_filename))
    
    print(f"Scanning for .env files in: {os.path.abspath(target_dir)}")
    
    with open(output_path, "w", encoding="utf-8") as outfile:
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file == ".env":
                    current_file_path = os.path.join(root, file)
                    
                    # Skip the output file to avoid self-appending if re-run
                    if os.path.abspath(current_file_path) == output_path:
                        continue
                    
                    relative_path = os.path.relpath(current_file_path, target_dir)
                    print(f"Found: {relative_path}")
                    
                    # Write separator header
                    outfile.write(f"\n# ==========================================\n")
                    outfile.write(f"# Source: {relative_path}\n")
                    outfile.write(f"# ==========================================\n\n")
                    
                    try:
                        with open(current_file_path, "r", encoding="utf-8") as infile:
                            content = infile.read()
                            outfile.write(content)
                            # Ensure there is a trailing newline before the next file
                            if content and not content.endswith("\n"):
                                outfile.write("\n")
                    except Exception as e:
                        print(f"  [ERROR] Could not read {relative_path}: {e}")

    print(f"\nSuccess! Consolidated file created at: {output_path}")

if __name__ == "__main__":
    # Runs in the current working directory by default
    combine_env_files()