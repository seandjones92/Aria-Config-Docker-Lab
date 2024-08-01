# Aria Config Docker Lab

Project to help run [Aria Automation Config](https://www.vmware.com/products/aria-automation/saltstack-config.html) in docker for testing and reference purposes.
This assumes you have already paid for, or are otherwise entitled, to the installables for this product at [VMware Customer Connect](https://customerconnect.vmware.com/home).
Environments created and managed by this project are not fit for production usage or anything resembling production usage, this is simply for self reference labs.

## Setup

Tell the script if you want an open source or enterprise lab. If you want an enterprise lab you will need to place the Aria Config installer tgz file at the root of the project.
If you want to run an open source lab no other external dependencies are needed, just an internet connection to pull Docker images and install packages into them.

```
usage: prep.py [-h] [-c] [-o] [-e] [salt_version]

positional arguments:
  salt_version       Which version of salt to use. Defaults to 3007.1

options:
  -h, --help         show this help message and exit
  -c, --clean        Clean up build dirs
  -o, --open-source  Prep open source bits
  -e, --enterprise   Prep enterprise bits
  ```

Once everything is up you can load the web UI at [localhost](http://localhost:8080)

## Factory reset

To reset your lab to a "like new" state run `./prep.py --clean`.
