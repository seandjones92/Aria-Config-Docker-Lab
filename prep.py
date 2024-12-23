#!/usr/bin/env python3

"""
Build and Deployment Script for OSS and Enterprise Configurations

This script manages the build and deployment environment using Docker Compose.
It handles environment cleanup, environment variable setup, preparation of
enterprise bundles, and user interaction for initiating Docker Compose operations.

Features:
- Clean existing environments and build directories
- Setup environment variables for OSS and Enterprise modes
- Prepare and extract enterprise installer bundles
- Create and manage symbolic links with absolute paths
- Interactive and non-interactive modes for Docker Compose execution
- Comprehensive logging with configurable log levels and output destinations
- Secure handling of sensitive credentials
- Dependency checks for required external tools
- Enhanced error handling and user feedback

Author: [Your Name]
Date: [Date]
"""

import os
import shutil
import subprocess
import tarfile
import glob
import argparse
import logging
import sys
import stat
from pathlib import Path
from typing import List, Optional, Dict
import getpass

# --------------------------- Configuration Constants --------------------------- #

# Define all paths and filenames as constants for easy modification
COMPOSE_FILE_NAME = 'compose.yaml'
OSS_COMPOSE_FILE = 'oss-compose.yaml'
ENTERPRISE_COMPOSE_FILE = 'aria-compose.yaml'  # Verify if 'aria' is correct or should be 'enterprise'
INSTALLER_BUNDLE_PATTERN = 'vRA_SaltStack_Config*.tar.gz'
ENV_FILE = '.env'
SYMLINKS = {
    'compose.yaml': {
        'oss': OSS_COMPOSE_FILE,
        'enterprise': ENTERPRISE_COMPOSE_FILE
    },
    'data/master.d': {
        'oss': 'data/oss-master',
        'enterprise': 'data/ent-master'
    }
}
DIRECTORIES_TO_REMOVE = [
    './build/sse-installer',
    './build/raas/eapi_service',
    './build/salt-master/eapi_plugin',
    'data/postgres',
    'data/raas/pki',
    'data/master/pki',
    'data/redis'
]
FILES_TO_REMOVE = [
    '.env',
    'data/raas/raas.secconf',
    'data/raas/initialized',
    'data/redis/redis.conf'
]
SYMLINKS_TO_REMOVE = list(SYMLINKS.keys())
REQUIRED_COMMANDS = ['docker']  # Removed 'docker-compose' as it's now a subcommand
DOCKER_COMPOSE_CMD = ['docker', 'compose']  # Using 'docker compose' as the command

# Default Salt version
DEFAULT_SALT_VERSION = '3006.9'

# Default credentials (to be overridden securely)
DEFAULT_POSTGRES_USER = "salteapi"

# ---------------------------------------------------------------------------- #

def setup_logging(log_level: str, log_file: Optional[str] = None):
    """
    Configures the logging settings.

    Args:
        log_level (str): The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file (Optional[str]): Path to the log file. If None, logs to stdout.
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        print(f"Invalid log level: {log_level}")
        sys.exit(1)
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=log_file,
        filemode='a' if log_file else 'w',
        force=True
    )

def check_dependencies():
    """
    Checks if all required external commands are available in the system PATH.
    Specifically checks for 'docker' and the 'docker compose' subcommand.
    Exits the script if any are missing.
    """
    missing = []
    for cmd in REQUIRED_COMMANDS:
        if shutil.which(cmd) is None:
            missing.append(cmd)
    if missing:
        logging.error(f"Missing required commands: {', '.join(missing)}. Please install them before running the script.")
        sys.exit(1)
    
    # Check if 'docker compose' subcommand is available
    try:
        subprocess.run(DOCKER_COMPOSE_CMD + ['version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logging.debug("'docker compose' subcommand is available.")
    except subprocess.CalledProcessError:
        logging.error("'docker compose' subcommand is not available. Ensure you have a recent version of Docker that includes 'compose' as a subcommand.")
        sys.exit(1)
    except FileNotFoundError:
        logging.error("'docker' command not found. Please install Docker.")
        sys.exit(1)

def get_script_directory() -> Path:
    """
    Returns the absolute path of the directory where the script resides.

    Returns:
        Path: Absolute path of the script's directory.
    """
    return Path(__file__).parent.resolve()

def clean_environment():
    """
    Cleans up existing build directories, environment files, and Docker Compose environments.
    """
    logging.info("Starting environment cleanup.")

    # Ensure the compose.yaml file exists before running docker compose down
    compose_path = Path(COMPOSE_FILE_NAME)
    if compose_path.exists():
        try:
            subprocess.run(DOCKER_COMPOSE_CMD + ['down', '-v', '--rmi', 'local'], check=True)
            logging.info("Docker Compose environment cleaned successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error cleaning up Docker environment: {e}")
    
    # Remove specified directories
    for directory in DIRECTORIES_TO_REMOVE:
        dir_path = Path(directory)
        if dir_path.exists() and dir_path.is_dir():
            try:
                shutil.rmtree(dir_path)
                logging.info(f"Removed directory: {directory}")
            except Exception as e:
                logging.error(f"Failed to remove directory {directory}: {e}")
        else:
            logging.debug(f"Directory {directory} does not exist. Skipping.")
    
    # Remove specified files
    for file in FILES_TO_REMOVE:
        file_path = Path(file)
        if file_path.exists() and file_path.is_file():
            try:
                file_path.unlink()
                logging.info(f"Removed file: {file}")
            except Exception as e:
                logging.error(f"Failed to remove file {file}: {e}")
        else:
            logging.debug(f"File {file} does not exist. Skipping.")
    
    # Remove specified symlinks
    for symlink in SYMLINKS_TO_REMOVE:
        symlink_path = Path(symlink)
        if symlink_path.is_symlink():
            try:
                symlink_path.unlink()
                logging.info(f"Removed symlink: {symlink}")
            except Exception as e:
                logging.error(f"Failed to remove symlink {symlink}: {e}")
        else:
            logging.debug(f"Symlink {symlink} does not exist. Skipping.")
    
    logging.info("Environment cleanup completed.")

def write_env_file(salt_version: str, enterprise: bool = False, credentials: Optional[Dict[str, str]] = None):
    """
    Creates or updates the .env file with necessary environment variables.

    Args:
        salt_version (str): The version of Salt to set in the .env file.
        enterprise (bool): Whether to include Enterprise-specific configurations.
        credentials (Optional[Dict[str, str]]): Dictionary containing sensitive credentials.
    """
    logging.info("Writing environment variables to .env file.")

    env_vars = {"SALT_VERSION": salt_version}

    if enterprise:
        # Handle Enterprise-specific configurations
        raas_rpm_paths = glob.glob('build/raas/eapi_service/files/raas*.rpm')
        if raas_rpm_paths:
            raas_rpm_name = os.path.basename(raas_rpm_paths[0])
            env_vars["RAAS_RPM_NAME"] = raas_rpm_name
            logging.debug(f"Set RAAS_RPM_NAME to {raas_rpm_name}")
        else:
            logging.warning("No RAAS RPM found. Enterprise configuration may be incomplete.")

        master_plugin_paths = glob.glob('build/salt-master/eapi_plugin/files/SSEAPE*.whl')
        if master_plugin_paths:
            master_plugin_name = os.path.basename(master_plugin_paths[0])
            env_vars["MASTER_PLUGIN_NAME"] = master_plugin_name
            logging.debug(f"Set MASTER_PLUGIN_NAME to {master_plugin_name}")
        else:
            logging.warning("No master plugin found. Enterprise configuration may be incomplete.")

        # Securely handle credentials
        if credentials and "POSTGRES_PASS" in credentials and "REDIS_PASSWORD" in credentials:
            env_vars.update(credentials)
            logging.debug("Added enterprise credentials to environment variables.")
        else:
            # Prompt the user for sensitive credentials if not provided
            logging.info("Prompting user for Enterprise credentials.")
            postgres_pass = getpass.getpass(prompt='Enter PostgreSQL Password: ')
            redis_password = getpass.getpass(prompt='Enter Redis Password: ')
            env_vars["POSTGRES_USER"] = DEFAULT_POSTGRES_USER
            env_vars["POSTGRES_PASS"] = postgres_pass
            env_vars["REDIS_PASSWORD"] = redis_password
            logging.debug("Collected Enterprise credentials from user.")

    # Read existing .env variables to update
    env_file_path = Path(ENV_FILE)
    existing_env = {}
    if env_file_path.exists():
        try:
            with env_file_path.open('r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        existing_env[key] = value
            logging.debug("Loaded existing .env variables.")
        except Exception as e:
            logging.error(f"Error reading existing .env file: {e}")
            sys.exit(1)

    # Update existing variables with new ones
    existing_env.update(env_vars)

    # Write updated environment variables to .env file
    try:
        with env_file_path.open('w') as env_file:
            for key, value in existing_env.items():
                env_file.write(f"{key}={value}\n")
        logging.info(".env file written successfully.")
    except Exception as e:
        logging.error(f"Error writing to .env file: {e}")
        sys.exit(1)

def print_file_contents(file_path: str):
    """
    Prints the contents of the specified file.

    Args:
        file_path (str): Path to the file to be printed.
    """
    logging.info(f"Displaying contents of {file_path}.")
    path = Path(file_path)
    if path.is_file():
        try:
            with path.open('r') as file:
                contents = file.read()
                print(contents)
                logging.debug(f"Contents of {file_path} displayed.")
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {e}")
    else:
        logging.warning(f"File {file_path} does not exist.")

def prepare_enterprise_bundle(script_dir: Path):
    """
    Extracts the installer bundle into the build directory and copies necessary installers.

    Args:
        script_dir (Path): The directory where the script resides.
    """
    logging.info("Preparing Enterprise bundle.")

    installer_bundles = list(script_dir.glob(INSTALLER_BUNDLE_PATTERN))
    if installer_bundles:
        installer_bundle = installer_bundles[0]
        try:
            with tarfile.open(installer_bundle, 'r:gz') as tar:
                tar.extractall(path=script_dir / 'build')
            logging.info(f"Enterprise bundle '{installer_bundle}' extracted successfully.")
        except tarfile.TarError as e:
            logging.error(f"Error extracting installer bundle '{installer_bundle}': {e}")
            sys.exit(1)
    else:
        logging.error("Installer bundle not found. Ensure the bundle exists before proceeding.")
        sys.exit(1)

    # Define source and destination directories
    src_eapi_service = script_dir / 'build/sse-installer/salt/sse/eapi_service'
    dest_eapi_service = script_dir / 'build/raas/eapi_service'
    src_eapi_plugin = script_dir / 'build/sse-installer/salt/sse/eapi_plugin'
    dest_eapi_plugin = script_dir / 'build/salt-master/eapi_plugin'

    # Copy installer directories
    try:
        shutil.copytree(src_eapi_service, dest_eapi_service, dirs_exist_ok=True)
        shutil.copytree(src_eapi_plugin, dest_eapi_plugin, dirs_exist_ok=True)
        logging.info("Enterprise installers copied successfully.")
    except FileNotFoundError as e:
        logging.error(f"Required installer directory not found: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error copying installer directories: {e}")
        sys.exit(1)

def create_symlink(target: str, link_name: str, script_dir: Path):
    """
    Creates a symbolic link with an absolute path.

    Args:
        target (str): The target file/directory the symlink points to.
        link_name (str): The name of the symlink to create.
        script_dir (Path): The directory where the script resides.
    """
    link_path = script_dir / link_name
    target_path = script_dir / target

    if not target_path.exists():
        logging.error(f"Target for symlink does not exist: {target_path}")
        sys.exit(1)

    if link_path.is_symlink() or link_path.exists():
        logging.debug(f"Symlink {link_name} already exists. Skipping creation.")
        return

    try:
        os.symlink(target_path, link_path)
        logging.info(f"Created symlink: {link_name} -> {target}")
    except OSError as e:
        logging.error(f"Failed to create symlink {link_name} -> {target}: {e}")
        sys.exit(1)

def prompt_docker_compose(non_interactive: bool = False, auto_confirm: bool = False):
    """
    Prompts the user to run Docker Compose and acts based on the input.
    In non-interactive mode, it can automatically proceed based on auto_confirm.

    Args:
        non_interactive (bool): If True, do not prompt the user.
        auto_confirm (bool): If True, automatically confirm actions in non-interactive mode.
    """
    if non_interactive:
        if auto_confirm:
            user_input = 'y'
            logging.debug("Non-interactive mode: auto-confirming Docker Compose execution.")
        else:
            logging.info("Non-interactive mode: skipping Docker Compose execution.")
            return
    else:
        # Interactive prompt
        try:
            user_input = input("Do you wish to run Docker Compose? (y/n): ").strip().lower()
        except EOFError:
            logging.warning("No input received. Skipping Docker Compose execution.")
            return

    if user_input in ['y', 'yes']:
        try:
            subprocess.run(DOCKER_COMPOSE_CMD + ['up', '-d'], check=True)
            logging.info("Docker Compose started successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error starting Docker Compose: {e}")
    elif user_input in ['n', 'no']:
        logging.info("Docker Compose will not be run.")
    else:
        logging.warning("Invalid input received. Docker Compose will not be run.")

def handle_oss_mode(script_dir: Path, salt_version: str, non_interactive: bool, auto_confirm: bool):
    """
    Handles the preparation for Open Source Software (OSS) mode.

    Args:
        script_dir (Path): The directory where the script resides.
        salt_version (str): The version of Salt to use.
        non_interactive (bool): If True, run in non-interactive mode.
        auto_confirm (bool): If True, automatically confirm actions in non-interactive mode.
    """
    logging.info("Handling OSS mode.")
    clean_environment()
    write_env_file(salt_version)

    # Create necessary symlinks with absolute paths
    create_symlink(SYMLINKS['compose.yaml']['oss'], 'compose.yaml', script_dir)
    create_symlink(SYMLINKS['data/master.d']['oss'], 'data/master.d', script_dir)

    print_file_contents(ENV_FILE)
    prompt_docker_compose(non_interactive, auto_confirm)

def handle_enterprise_mode(script_dir: Path, salt_version: str, non_interactive: bool, auto_confirm: bool):
    """
    Handles the preparation for Enterprise mode.

    Args:
        script_dir (Path): The directory where the script resides.
        salt_version (str): The version of Salt to use.
        non_interactive (bool): If True, run in non-interactive mode.
        auto_confirm (bool): If True, automatically confirm actions in non-interactive mode.
    """
    logging.info("Handling Enterprise mode.")
    clean_environment()
    prepare_enterprise_bundle(script_dir)

    # Collect credentials securely
    credentials = {
        "POSTGRES_USER": DEFAULT_POSTGRES_USER,
        # POSTGRES_PASS and REDIS_PASSWORD will be collected inside write_env_file
    }

    write_env_file(salt_version, enterprise=True, credentials=credentials)

    # Create necessary symlinks with absolute paths
    create_symlink(SYMLINKS['compose.yaml']['enterprise'], 'compose.yaml', script_dir)
    create_symlink(SYMLINKS['data/master.d']['enterprise'], 'data/master.d', script_dir)

    print_file_contents(ENV_FILE)
    prompt_docker_compose(non_interactive, auto_confirm)

def handle_signals():
    """
    Handles termination signals to perform graceful shutdowns if necessary.
    """
    import signal

    def signal_handler(sig, frame):
        logging.info("Script interrupted by user. Exiting gracefully.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """
    Main function to control the script logic.
    """
    # Handle termination signals for graceful shutdown
    handle_signals()

    # Argument parsing setup
    parser = argparse.ArgumentParser(
        description="Build and Deployment Script for OSS and Enterprise Configurations"
    )
    parser.add_argument(
        '-c', '--clean',
        help='Clean up build directories and environment.',
        action='store_true'
    )
    parser.add_argument(
        '-e', '--enterprise',
        help='Prepare Enterprise configurations.',
        action='store_true'
    )
    parser.add_argument(
        '-s', '--salt-version',
        default=DEFAULT_SALT_VERSION,
        help=f"Specify the Salt version to use. Defaults to {DEFAULT_SALT_VERSION}."
    )
    parser.add_argument(
        '-n', '--non-interactive',
        help='Run the script in non-interactive mode.',
        action='store_true'
    )
    parser.add_argument(
        '-a', '--auto-confirm',
        help='Automatically confirm prompts in non-interactive mode.',
        action='store_true'
    )
    parser.add_argument(
        '--log-level',
        default='ERROR',
        help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Defaults to ERROR.'
    )
    parser.add_argument(
        '--log-file',
        help='Path to a file where logs will be written. If not set, logs are printed to stdout.'
    )
    args = parser.parse_args()

    # Setup logging based on user arguments
    setup_logging(args.log_level, args.log_file)

    logging.debug(f"Script arguments: {args}")

    # Check for required external dependencies
    check_dependencies()

    # Get the script's directory
    script_dir = get_script_directory()

    # Clean environment if the '--clean' flag is set
    if args.clean:
        clean_environment()
        logging.info("Build environment cleaned.")
        sys.exit(0)

    # Handle enterprise mode if the '--enterprise' flag is set
    if args.enterprise:
        handle_enterprise_mode(
            script_dir,
            salt_version=args.salt_version,
            non_interactive=args.non_interactive,
            auto_confirm=args.auto_confirm
        )
        sys.exit(0)

    # Handle OSS mode by default
    handle_oss_mode(
        script_dir,
        salt_version=args.salt_version,
        non_interactive=args.non_interactive,
        auto_confirm=args.auto_confirm
    )

if __name__ == "__main__":
    main()

