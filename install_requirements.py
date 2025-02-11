import os
import subprocess
import sys

def install_requirements():
    requirements_file = "requirements.txt"
    
    # Check if requirements.txt exists
    if not os.path.exists(requirements_file):
        print("Error: requirements.txt not found! Make sure it's in the same folder as this script.")
        input("Press Enter to exit...")
        return
    
    # Install dependencies
    print("Installing required libraries...\n")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file], creationflags=subprocess.CREATE_NO_WINDOW)
        print("\n✅ All dependencies installed successfully!")
    except subprocess.CalledProcessError:
        print("\n❌ Error installing dependencies. Please check your internet connection and try again.")
    
    input("\nInstallation complete. Press Enter to exit...")

if __name__ == "__main__":
    install_requirements()
