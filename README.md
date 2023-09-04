# Aria Config Docker Lab

Project to help run [Aria Automation Config](https://www.vmware.com/products/aria-automation/saltstack-config.html) in docker for testing and reference purposes. This assumes you have already paid for, or are otherwise entitled, to the installables for this product at [VMware Customer Connect](https://customerconnect.vmware.com/home). Environments created and managed by this project are not fit for production usage or anything resembling production usage, this is simply for self reference labs.

## Setup

To get started download the `*.tar` installable for el9 and place it in root of the project. Then run the `prep.sh` script. This will unpack the installer tar into the proper locations and will build an `.env` file for docker.
Once that is completed run `docker compose up -d`. After the containers are started it will take about 2 minutes for first time bootstrapping to complete.

Once everything is up you can load the web UI at [localhost](http://localhost:8080)

## Factory reset

To reset your lab to a "like new" state run `./reset.sh`.
