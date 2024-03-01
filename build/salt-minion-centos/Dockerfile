FROM quay.io/centos/centos:stream9
ARG salt_version
RUN rpm --import https://repo.saltproject.io/salt/py3/redhat/9/x86_64/SALT-PROJECT-GPG-PUBKEY-2023.pub
RUN curl -fsSL https://repo.saltproject.io/salt/py3/redhat/9/x86_64/minor/$salt_version.repo | tee /etc/yum.repos.d/salt.repo
RUN yum update -y
RUN yum install -y salt-minion
ENTRYPOINT [ "/usr/bin/salt-minion" ]
CMD [ "-l", "info" ]

