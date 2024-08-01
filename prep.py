#!/usr/bin/env python3

import os
import shutil
import subprocess
import tarfile
import glob
import sys
import argparse
from html.parser import HTMLParser
import urllib.request


# TODO: need to have a doctor function that checks to make sure docker and any other tooling needs to be present

# TODO: Eventually replace need for dockerfiles and just generate them at prep time
class ComposeBuilder():
    """
    Build out a compose file based on the methods used.
    """


def print_help_message():
    """
    Displays the help message for the script.
    """
    print("Usage: prep.py [OPTIONS] SALT_VERSION")
    print("Extracts the installer bundle and prepares the build directories.")
    print("")
    print("Options:")
    print("  --oss    Only prep open source bits")
    print("  --ent    Prep enterprise bits")
    print("  --clean  Clean up build dirs")
    print("  --help   Display this help message.")
    print("")
    print("SALT_VERSION Optional. Specify the full version of salt to install")

def clean_environment():
    """
    Cleans up existing build directories and environment files.
    """
    if os.path.exists('compose.yaml'):
        subprocess.run(['docker', 'compose', 'down'])

    directories_to_remove = [
        './build/sse-installer',
        './build/raas/eapi_service',
        './build/salt-master/eapi_plugin',
        'data/postgres',
        'data/raas/pki',
        'data/master/pki',
        'data/redis'
    ]

    files_to_remove = [
        '.env',
        'compose.yaml',
        'data/raas/raas.secconf',
        'data/raas/initialized',
        'data/redis/redis.conf'
    ]

    # Delete directories specified in 'directories_to_remove'
    for directory in directories_to_remove:
        shutil.rmtree(directory, ignore_errors=True)

    # Delete files specified in 'files_to_remove'
    for file in files_to_remove:
        if os.path.isfile(file):
            os.remove(file)

def write_env_file(salt_version, enterprise=False):
    """
    Builds and populates the .env file with configurations.

    salt_version - string - the version of salt to set in env file
    enterprise - bool - set to true to build an enterprise env file
    """
    env_vars = {}

    env_vars["SALT_VERSION"] = salt_version

    if enterprise:
        raas_rpm_path = glob.glob('build/raas/eapi_service/files/raas*.rpm')[0]
        raas_rpm_name = os.path.basename(raas_rpm_path)
        env_vars["RAAS_RPM_NAME"] = raas_rpm_name

        master_plugin_path = glob.glob('build/salt-master/eapi_plugin/files/SSEAPE*.whl')[0]
        master_plugin_name = os.path.basename(master_plugin_path)
        env_vars["MASTER_PLUGIN_NAME"] = master_plugin_name

        env_vars["POSTGRES_USER"] = "salteapi"
        env_vars["POSTGRES_PASS"] = "abc123"
        env_vars["REDIS_PASSWORD"] = "def456"

    # put all env values in a dictionary and if the key is populated write the value, otherwise skip
    with open('.env', 'a') as env_file:
        for env_var in env_vars:
            env_file.write(f"{env_var}={env_vars[env_var]}\n")

def print_file_contents(file_path):
    """
    Prints the contents of the specified file.
    """
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            print(file.read())
    else:
        print(f"{file_path} does not exist.")

def create_symlink(source, link_name):
    """
    Creates a symbolic link from source to link_name.
    """
    try:
        os.symlink(source, link_name)
    except FileExistsError:
        print('Cannot create symlink, file already exists.')

def extract_enterprise_bundle():
    """
    Extracts the installer bundle into the build directory.
    """
    installer_bundle = glob.glob('vRA_SaltStack_Config*.tar.gz')
    if installer_bundle:
        with tarfile.open(installer_bundle[0], 'r:gz') as tar:
            tar.extractall(path='build')
    else:
        print("Installer bundle not found.")

def copy_enterprise_installers():
    """
    Copies installer files to the appropriate build directories.
    """
    shutil.copytree('build/sse-installer/salt/sse/eapi_service', 'build/raas/eapi_service')
    shutil.copytree('build/sse-installer/salt/sse/eapi_plugin', 'build/salt-master/eapi_plugin')

def prompt_docker_compose():
    """
    Prompts the user to run Docker Compose and acts based on the input.
    """
    while True:
        yn = input("Do you wish to run docker compose? ").lower()
        if yn in ['y', 'yes']:
            subprocess.run(['docker', 'compose', 'up', '-d'])
            break
        elif yn in ['n', 'no']:
            return
        else:
            print("Please answer yes or no.")

def handle_oss_mode(salt_version):
    """
    Handles the preparation for open-source bits.

    salt_version - string - version of salt to use
    """
    clean_environment()
    write_env_file(salt_version)
    create_symlink('oss-compose.yaml', 'compose.yaml')
    print_file_contents('.env')
    prompt_docker_compose()

def handle_enterprise_mode(salt_version):
    """
    Handles the preparation for enterprise bits.

    salt_version - string - version of salt to use
    """
    clean_environment()
    extract_enterprise_bundle()
    copy_enterprise_installers()
    write_env_file(salt_version, enterprise=True)
    create_symlink('aria-compose.yaml', 'compose.yaml')
    print_file_contents('.env')
    prompt_docker_compose()

def find_salt_versions():
    # reach out to https://repo.saltproject.io/salt/py3/src/ to find the latest version of salt
    # TODO: maybe instead this should check salt bootstrap for available versions since I will be retooling around that anyways
    with urllib.request.urlopen('https://repo.saltproject.io/salt/py3/src/') as f:
        htmlbytes = f.read()
        htmlstring = htmlbytes.decode("utf-8")

    class MyHTMLParser(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == "a":
                for name, value in attrs:
                    if name == "href":
                        print(value)
    parser = MyHTMLParser()
    parser.feed(htmlstring)

def main():
    """
    Main function to control the script logic.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clean', help='Clean up build dirs', action='store_true')
    parser.add_argument('-o', '--open-source', help='Prep open source bits', action='store_true')
    parser.add_argument('-e', '--enterprise', help='Prep enterprise bits', action='store_true')
    parser.add_argument('salt_version', nargs='?', default='3007.1', help='Which version of salt to use. Defaults to 3007.1')
    args = parser.parse_args()

    if args.clean:
        clean_environment()
        print("Build environment cleaned")
        return

    if args.open_source:
        handle_oss_mode(args.salt_version)
        return

    if args.enterprise:
        handle_enterprise_mode(args.salt_version)
        return

if __name__ == "__main__":
    main()
