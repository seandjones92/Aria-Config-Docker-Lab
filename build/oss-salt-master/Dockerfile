FROM ubuntu:22.04
ARG salt_version
RUN apt-get update
RUN apt-get install -y curl
RUN curl -fsSL -o /etc/apt/keyrings/salt-archive-keyring-2023.gpg https://repo.saltproject.io/salt/py3/ubuntu/22.04/amd64/SALT-PROJECT-GPG-PUBKEY-2023.gpg
RUN echo "deb [signed-by=/etc/apt/keyrings/salt-archive-keyring-2023.gpg arch=amd64] https://repo.saltproject.io/salt/py3/ubuntu/22.04/amd64/minor/$salt_version jammy main" | tee /etc/apt/sources.list.d/salt.list
RUN apt-get update
RUN apt-get install -y salt-master
ENTRYPOINT [ "/usr/bin/salt-master" ]
CMD [ "-l", "info" ]

