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

Once the containers are built go to the `salt-lab` directory and run `docker compose up -d`. It will take about 2 minutes for everything to initialize within the containers. Subsequent restarts are much faster as first time bootstrapping does not need to be done.

To reset your lab to a "like new" state use the `reset.sh` script in `salt-lab`.

## To-Do

- create script to export/import DB
- create script to backup/deploy all config files
- import initial DB content as part of init
