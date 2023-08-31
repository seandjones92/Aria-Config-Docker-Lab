# Aria Config Docker Lab

Project to help run [Aria Automation Config](https://www.vmware.com/products/aria-automation/saltstack-config.html) in docker for testing and reference purposes. This assumes you have already paid for, or are otherwise entitled, to the installables for this product at [VMware Customer Connect](https://customerconnect.vmware.com/home). Environments created and managed by this project are not fit for production usage or anything resembling production usage, this is simply for self reference labs.

## Setup

To get started download the `*.tar.gz` installable for el9 and place it in the `containers` directory. For example:

```bash
$ ls -1
README.md
build-containers.sh
raas
salt-master
vRA_SaltStack_Config-8.13.0.4-1.el9_Installer.tar.gz
```

Then run the following command to build out your `raas` and `salt-master` docker images from the provided installable bundle:

```bash
./build-containers.sh vRA_SaltStack_Config-8.13.0.4-1.el9_Installer.tar.gz
```

Once the containers are built navigate to the `salt-lab` directory and set the desired postgres credentials in `compose.yaml`, and set the desired redis password in `redis/redis.conf`. With the credentials for the DB and cache set and known, run the `save_creds.sh` script and provide the credentials. The user name for redis is "default". This will create the `raas/raas.seconf` file that the raas process needs to authenticate to the postgres and redis services.

Once the `save_creds.sh` script completes you can bring the lab up with `docker compose up -d` and access it at [localhost:8080](http://localhost:8080). Note that there are no certificates applied to any of the components deployed here.

## To-Do

- create script to export/import DB
- create script to backup/deploy all config files
- import initial DB content as part of init
