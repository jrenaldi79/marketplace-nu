import argparse
import os
import shutil
import platform
import subprocess

SSH_TEMPLATE_MAC = """
Host claude-box
    HostName {ip_address}
    User student
    IdentityFile {key_path}
    RequestTTY yes
    RemoteCommand tmux new -A -s claude-session
    LocalForward 10445 127.0.0.1:445
"""

SSH_TEMPLATE_WIN = """
Host claude-box
    HostName {ip_address}
    User student
    IdentityFile {key_path}
    RequestTTY yes
    RemoteCommand tmux new -A -s claude-session
"""

RDP_TEMPLATE = """full address:s:{ip_address}
username:s:student
prompt for credentials:i:1
"""

def check_rdp_client():
    os_name = platform.system()
    if os_name == "Darwin":
        # Check for Microsoft Remote Desktop or Windows App
        mrd_path = "/Applications/Microsoft Remote Desktop.app"
        win_app_path = "/Applications/Windows App.app"
        
        if os.path.exists(mrd_path) or os.path.exists(win_app_path):
            return True, "macOS RDP Client found."
        else:
            return False, "macOS RDP Client NOT found. Please install 'Microsoft Remote Desktop' or 'Windows App' from the Mac App Store."
    elif os_name == "Windows":
        return True, "Windows has native RDP support."
    else:
        return True, f"Running on {os_name}. Please ensure you have an RDP client like Remmina installed."

def test_ssh_connection():
    print("\n--- Testing SSH Connection ---")
    print("Testing terminal access to the server...")
    try:
        # We use BatchMode=yes to fail fast instead of prompting for passwords if key auth fails
        result = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=accept-new", "-o", "BatchMode=yes", "claude-box", "echo '✅ Connection Successful'"],
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode == 0 and "Connection Successful" in result.stdout:
            print("✅ Successfully connected to your server!")
            return True
        else:
            print("❌ Connection test failed.")
            print(f"Error details: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Connection test timed out.")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return False

def print_troubleshooting():
    print("\n--- Troubleshooting Guide ---")
    print("If your SSH connection failed, please check the following:")
    print("1. Did you enter the correct IP address?")
    print("2. Is your internet connection active?")
    print("3. Are you connected to a network that blocks SSH (Port 22)? Try a different Wi-Fi or hotspot.")
    print("4. Did you select the correct Private SSH Key file?")
    print("\nTo try again, simply re-run this setup script.")
    print("===========================================")

def main():
    parser = argparse.ArgumentParser(description="Configure local SSH client to connect to your Claude VPS.")
    parser.add_argument("ip_address", help="The IP address of your server")
    parser.add_argument("key_path", help="The path to the private SSH key file you downloaded")
    args = parser.parse_args()

    # Expand paths
    source_key_path = os.path.expanduser(args.key_path)
    if not os.path.exists(source_key_path):
        print(f"Error: Could not find the SSH key file at {source_key_path}")
        return

    # Create ~/.ssh if it doesn't exist
    ssh_dir = os.path.expanduser("~/.ssh")
    os.makedirs(ssh_dir, exist_ok=True)
    os.chmod(ssh_dir, 0o700)

    # Copy the key to ~/.ssh and set correct permissions
    dest_key_path = os.path.join(ssh_dir, "student_claude_key")
    shutil.copy2(source_key_path, dest_key_path)
    os.chmod(dest_key_path, 0o600)
    print(f"✅ Copied SSH key to {dest_key_path} and set secure permissions.")

    # Update ~/.ssh/config
    config_path = os.path.join(ssh_dir, "config")
    
    os_name = platform.system()
    if os_name == "Darwin":
        config_entry = SSH_TEMPLATE_MAC.format(ip_address=args.ip_address, key_path=dest_key_path)
    else:
        config_entry = SSH_TEMPLATE_WIN.format(ip_address=args.ip_address, key_path=dest_key_path)
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            content = f.read()
        if "Host claude-box" not in content:
            with open(config_path, 'a') as f:
                f.write(config_entry)
            print(f"✅ Appended configuration to {config_path}.")
        else:
            print("⚠️ A host named 'claude-box' already exists in your ~/.ssh/config file. Skipping SSH config update.")
    else:
        with open(config_path, 'a') as f:
            f.write(config_entry)
        print(f"✅ Appended configuration to {config_path}.")

    # Configure Visual Desktop (RDP)
    print("\n--- Visual Desktop (RDP) Setup ---")
    rdp_supported, rdp_msg = check_rdp_client()
    print(rdp_msg)
    
    desktop_dir = os.path.expanduser("~/Desktop")
    if not os.path.exists(desktop_dir):
        desktop_dir = os.path.expanduser("~")
        
    rdp_file_path = os.path.join(desktop_dir, "Claude-Box-Visual.rdp")
    with open(rdp_file_path, "w") as f:
        f.write(RDP_TEMPLATE.format(ip_address=args.ip_address))
    
    print(f"✅ Created a Remote Desktop shortcut at: {rdp_file_path}")

    # Configure Google Drive Sync
    print("\n--- Google Drive Sync Setup ---")
    print("This allows you to sync your code automatically to your personal Google Drive.")
    print("1. Run this command in a NEW terminal window on your computer (NOT on the server):")
    print("   rclone authorize \"drive\"")
    print("2. A browser will open. Log in to Google and click 'Allow'.")
    print("3. After you allow, your terminal will print a block of code starting with '{\"access_token\":...}'")
    print("\nPaste that ENTIRE block of code here (or press Enter to skip):")
    
    try:
        auth_code = input().strip()
        if auth_code and auth_code.startswith("{"):
            print("Configuring Google Drive on your server...")
            
            # Create the rclone.conf locally to push it
            rclone_conf_content = f"[gdrive]\ntype = drive\nscope = drive\ntoken = {auth_code}\n"
            temp_conf = "rclone_temp.conf"
            with open(temp_conf, "w") as f:
                f.write(rclone_conf_content)
            
            # Push to VPS
            subprocess.run(["scp", temp_conf, f"root@{args.ip_address}:/home/student/.config/rclone/rclone.conf"], capture_output=True)
            os.remove(temp_conf)
            
            # Set permissions and setup service
            setup_cmds = [
                "chown student:student /home/student/.config/rclone/rclone.conf",
                "cat << 'EOF' > /etc/systemd/system/rclone-gdrive.service\n[Unit]\nDescription=RClone Mount Google Drive\nAfter=network-online.target\n\n[Service]\nType=simple\nUser=student\nExecStart=/usr/bin/rclone mount gdrive: /home/student/projects/GoogleDrive --vfs-cache-mode writes --vfs-cache-max-age 24h --vfs-cache-max-size 10G --allow-other --dir-cache-time 1m\nExecStop=/bin/fusermount -u /home/student/projects/GoogleDrive\nRestart=always\nRestartSec=10\n\n[Install]\nWantedBy=default.target\nEOF",
                "systemctl daemon-reload",
                "systemctl enable rclone-gdrive",
                "systemctl start rclone-gdrive"
            ]
            
            full_setup_cmd = " && ".join(setup_cmds)
            subprocess.run(["ssh", "-o", "RemoteCommand=none", f"root@{args.ip_address}", full_setup_cmd], capture_output=True)
            print("✅ Google Drive is now configured and will automatically mount to 'projects/GoogleDrive' on your server!")
        else:
            print("ℹ️ Skipping Google Drive setup. You can set it up manually later using 'rclone config' on the server.")
    except EOFError:
        pass

    print("\n🎉 Setup Complete! 🎉")
    print("\n🖥️  TERMINAL ACCESS (SSH):")
    print("   Open your terminal and type:  ssh claude-box")
    print("   (This will automatically log you in and start/resume your tmux session!)")
    
    print("\n📁 LOCAL FILE ACCESS (Native Network Drive):")
    print("   1. First, run 'ssh claude-box' in a terminal and keep it open (this opens the secure tunnel).")
    if platform.system() == "Darwin":
        print("   2. In Finder, press Cmd+K and enter: smb://student@127.0.0.1:10445/workspace")
    elif platform.system() == "Windows":
        print("   2. In File Explorer, map a drive to: \\\\127.0.0.1@10445\\workspace")
    print("   3. Enter your Visual Desktop Password when prompted.")
    
    print("\n🖼️  VISUAL DESKTOP ACCESS (RDP):")
    if platform.system() == "Darwin" and not rdp_supported:
        print("   1. First, install 'Microsoft Remote Desktop' from the Mac App Store.")
    print(f"   Double-click the file '{rdp_file_path}' to connect.")
    print("   When prompted, enter your provided Visual Desktop Password.")
    print("\n===========================================")

    # File Browsing Recommendation
    print("\n--- File Browsing & Editing ---")
    print("For the best experience editing files on your server, we strongly recommend using Visual Studio Code:")
    print("1. Download and install VS Code (https://code.visualstudio.com/)")
    print("2. Install the 'Remote - SSH' extension")
    print("3. Click the Remote Explorer icon, and connect to 'claude-box'")
    print("VS Code will automatically open your remote files just like a local folder!")
    print("===========================================")

    # Claude Desktop Instructions
    print("\n--- Claude Desktop (AI Agent) Setup ---")
    print("To use the Claude Desktop app with your new server:")
    print("1. Open the Claude Desktop app on your computer.")
    print("2. Click the 'SSH' or 'Remote' icon (usually in the bottom left or settings).")
    print("3. When prompted for a 'Host', simply type:  claude-box")
    print("4. Claude will automatically use your configured SSH key and connect!")
    print("===========================================")

    # Test the SSH connection
    connection_successful = test_ssh_connection()
    if not connection_successful:
        print_troubleshooting()
        return

    # Optionally attempt to open the RDP file if client is installed
    if rdp_supported:
        print("\nWould you like to test the Visual Desktop connection now? (y/n)")
        try:
            # Note: since this runs in a non-interactive pipe sometimes, we handle EOFError gracefully
            choice = input().strip().lower()
            if choice == 'y':
                print("Launching Remote Desktop...")
                if platform.system() == "Darwin":
                    subprocess.run(["open", rdp_file_path])
                elif platform.system() == "Windows":
                    os.startfile(rdp_file_path)
        except EOFError:
            pass

if __name__ == "__main__":
    main()
