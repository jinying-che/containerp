import os
import subprocess
import shutil

# Configuration
CONTAINER_ROOT = "/tmp/my_container_root"
CGROUP_PATH = "/sys/fs/cgroup/mycontainer"
MEMORY_LIMIT = "100M"  # 100MB memory limit
CPU_LIMIT = "50000"    # 50% of one CPU core (in microseconds)

def setup_filesystem():
    """Create a minimal filesystem if not present."""
    if not os.path.exists(CONTAINER_ROOT):
        print(f"Creating minimal filesystem at {CONTAINER_ROOT}...")
        subprocess.run([
            "debootstrap", "--variant=minbase", "buster", CONTAINER_ROOT,
            "http://deb.debian.org/debian/"
        ], check=True)
    else:
        print(f"Filesystem already exists at {CONTAINER_ROOT}.")

def setup_proc():
    """Ensure /proc exists inside the container root."""
    proc_path = os.path.join(CONTAINER_ROOT, "proc")
    os.makedirs(proc_path, exist_ok=True)

def setup_cgroup():
    """Configure cgroup v2 for memory and CPU restrictions."""
    print("Setting up cgroups...")
    os.makedirs(CGROUP_PATH, exist_ok=True)

    # Enable the cgroup for the current process
    with open(os.path.join(CGROUP_PATH, "cgroup.procs"), "w") as f:
        f.write(str(os.getpid()))

    # Set memory limit
    with open(os.path.join(CGROUP_PATH, "memory.max"), "w") as f:
        f.write(MEMORY_LIMIT)

    # Set CPU limit
    with open(os.path.join(CGROUP_PATH, "cpu.max"), "w") as f:
        f.write(f"{CPU_LIMIT} 100000")  # 50% CPU quota (period = 100000us)

def cleanup():
    """Cleanup cgroups and unmount /proc after container stops."""
    print("Cleaning up resources...")
    try:
        subprocess.run(["umount", "-l", os.path.join(CONTAINER_ROOT, "proc")], check=True)
    except subprocess.CalledProcessError:
        print("Warning: Could not unmount /proc, it might have been unmounted already.")
    shutil.rmtree(CGROUP_PATH, ignore_errors=True)

def run_container():
    """Run an isolated container environment."""
    print("Starting container...")

    command = [
        "unshare",              # Isolate namespaces
        "--mount",              # Isolate mount namespace
        "--pid",                # Isolate process namespace
        "--fork",               # Fork a new PID namespace
        "--uts",                # Isolate hostname
        "--mount-proc",         # Mount /proc
        "chroot",               # Change root to the container's filesystem
        CONTAINER_ROOT,         # Path to minimal filesystem
        "/bin/bash"             # Start bash shell inside the container
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running container: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("❗ This script requires root privileges. Please run as sudo.")
        exit(1)

    try:
        setup_filesystem()
        setup_proc()
        setup_cgroup()
        run_container()
    except Exception as e:
        print(f"An error occurred: {e}")
        cleanup()

