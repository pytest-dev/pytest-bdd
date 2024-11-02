import glob
import os
import subprocess
from functools import wraps
from itertools import chain


def _check_subprocess(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    return wrapper


def get_npm_root(global_install=False):
    command = "npm root -g" if global_install else "npm root"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()


@_check_subprocess
def check_npm():
    command = "npm --version"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()


@_check_subprocess
def check_npm_package(package_name, global_install=False):
    command = f'npm list -g "{package_name}"' if global_install else f"npm list {package_name}"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()


def find_resource(package_name, resource_path):
    # Check local node_modules
    local_npm_root = get_npm_root(global_install=False)
    local_resource_path = os.path.join(local_npm_root, package_name, resource_path)
    local_files = glob.iglob(local_resource_path)

    # Check global node_modules
    global_npm_root = get_npm_root(global_install=True)
    global_resource_path = os.path.join(global_npm_root, package_name, resource_path)
    global_files = glob.iglob(global_resource_path)

    return chain(local_files, global_files)
