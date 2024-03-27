FROM fedora:39
ARG salt_version
RUN rpm --import https://repo.saltproject.io/salt/py3/fedora/38/x86_64/SALT-PROJECT-GPG-PUBKEY-2023.pub
RUN curl -fsSL https://repo.saltproject.io/salt/py3/fedora/38/x86_64/minor/$salt_version.repo | tee /etc/yum.repos.d/salt.repo
RUN dnf update -y
RUN dnf install -y salt-minion
ENTRYPOINT [ "/usr/bin/salt-minion" ]
CMD [ "-l", "info" ]
