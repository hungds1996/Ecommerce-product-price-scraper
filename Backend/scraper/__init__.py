from main import main, load_auth
import sys
import subprocess


if __name__ == "__main__":
    # Extract command-line arguments
    if len(sys.argv) < 3:
        print('Usage: python -m package_name url search_text endpoint')
        sys.exit(1)
    
    url = sys.argv[1]
    search_text = sys.argv[2]
    endpoint = sys.argv[3]
    
    driver = load_auth()
    command = f"python main.py {url} \"{search_text}\" /results"
    subprocess.Popen(command, shell=True)