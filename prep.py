#!/usr/bin/env python3

import os
import shutil
import subprocess
import tarfile
import glob
import sys

# add a --config flag
# when you use this it creates an ini config file to specify env values and stuff
# if the file is present do not run prep.py interactively, but instead provide values in config file

# Eventually replace need for dockerfiles and just generate them at prep time
class ComposeBuilder():
    """
    Build out a compose file based on the methods used.
    """

    def postgres_db_template(self, psql_version, pg_password, pg_user, logging_size, logging_files):
        """
        Postgres service compose.yaml template

        psql_version:      postgres version. default 15.4
        pg_password:       pg password. default postgres123
        pg_user:           pg user. default salteapi
        logging_size:      size of logs before rolling. default 200k
        logging_files:     number of rolled logs to retain. default 5
        """
        version = "15.4"
        psql_template = """
  postgres:
    image: postgres:${version}
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASS}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    logging:
      options:
        max-size: "200k"
        max-file: "5"
"""

def help_message():
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
        'data/raas/raas.secconf',
        'data/raas/initialized',
        'data/master/pki',
        'data/redis'
    ]

    for directory in directories_to_remove:
        shutil.rmtree(directory, ignore_errors=True)

    files_to_remove = [
        '.env',
        'compose.yaml',
        'data/redis/redis.conf'
    ]

    for file in files_to_remove:
        if os.path.isfile(file):
            os.remove(file)


# collapse these two env_file functions into one that is more dynamic
def oss_env_file(salt_version='3007.0'):
    """
    Creates and populates the .env file with necessary configurations.
    """
    with open('.env', 'w') as env_file:
        env_file.write(f"SALT_VERSION={salt_version}\n")

def enterprise_env_file(salt_version='3007.0'):
    """
    Builds and populates the .env file with additional configurations.
    """
    raas_rpm_path = glob.glob('build/raas/eapi_service/files/raas*.rpm')[0]
    raas_rpm_name = os.path.basename(raas_rpm_path)
    master_plugin_path = glob.glob('build/salt-master/eapi_plugin/files/SSEAPE*.whl')[0]
    master_plugin_name = os.path.basename(master_plugin_path)

    with open('.env', 'a') as env_file:
        env_file.write(f"RAAS_RPM_NAME={raas_rpm_name}\n")
        env_file.write(f"MASTER_PLUGIN_NAME={master_plugin_name}\n")
        env_file.write(f"SALT_VERSION={salt_version}\n")
        env_file.write("POSTGRES_USER=default\n")
        env_file.write("POSTGRES_PASS=postgres123\n")

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
        print('Cannot create symlink, file already exists')

def extract_installer_bundle():
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

def configure_redis():
    """
    Configures the Redis configuration file.
    """
    os.makedirs('data/redis', exist_ok=True)
    with open('data/redis/redis.conf', 'w') as redis_conf:
        redis_conf.write("REDIS_PASS=redis123\n")

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

def handle_oss_mode(args):
    """
    Handles the preparation for open-source bits.
    """
    salt_version = '3007.0'
    if len(args) == 2:
        salt_version = args[1]
    oss_env_file(salt_version)
    create_symlink('oss-compose.yaml', 'compose.yaml')
    prompt_docker_compose()

def handle_enterprise_mode(args):
    """
    Handles the preparation for enterprise bits.
    """
    extract_installer_bundle()
    copy_enterprise_installers()
    # setting salt version should also be a function
    salt_version = '3007.0'
    if len(args) > 0:
        salt_version = args[0]
    enterprise_env_file(salt_version)
    configure_redis()
    create_symlink('aria-compose.yaml', 'compose.yaml')
    print_file_contents('.env')
    print_file_contents('data/redis/redis.conf')
    prompt_docker_compose()

def main():
    """
    Main function to control the script logic.
    """
    args = sys.argv[1:]


    if '--clean' in args:
        clean_environment()
        print("environment cleaned")
        return

    if '--oss' in args:
        clean_environment()
        handle_oss_mode(args)
        return

    if '--ent' in args:
        handle_enterprise_mode(args)
        return

    # handling help could be better
    if '--help' in args:
        help_message()
        return

    help_message()

if __name__ == "__main__":
    main()
