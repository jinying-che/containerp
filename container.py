import os
import sys
import subprocess

# Constants
CONTAINER_ROOT = "/tmp/my_container"
HOSTNAME = "tiny-container"

def setup_filesystem():
    """Creates an isolated root filesystem for the container."""
    os.makedirs(CONTAINER_ROOT, exist_ok=True)
    subprocess.run(["debootstrap", "--variant=minbase", "buster", CONTAINER_ROOT], check=True)
    print(f"Filesystem created at {CONTAINER_ROOT}")

def run_container():
    """Creates an isolated container environment using namespaces and chroot."""
    print("Starting container...")

    # Unshare namespaces (PID, Mount, UTS)
    flags = os.CLONE_NEWPID | os.CLONE_NEWNS | os.CLONE_NEWUTS
    pid = os.fork()

    if pid == 0:  # Child process (container process)
        os.unshare(flags)
        os.chroot(CONTAINER_ROOT)  # Change root filesystem
        os.chdir("/")  # Move to the new root
        subprocess.run(["hostname", HOSTNAME])

        # Mount proc to provide process info inside the container
        # subprocess.run(["mount", "-t", "proc", "proc", "/proc"], check=True)
        # os.system("mount -t proc proc /proc")

        # Run a shell inside the container
        subprocess.run(["/bin/bash"])
    else:
        os.waitpid(pid, 0)  # Wait for the child process to exit
        print("Container stopped.")

if __name__ == "__main__":
    if not os.path.exists(CONTAINER_ROOT + "/bin/bash"):
        print("Setting up the container filesystem...")
        setup_filesystem()

    run_container()

