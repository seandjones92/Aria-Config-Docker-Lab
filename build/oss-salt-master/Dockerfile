FROM almalinux:9.4-20240923
ARG salt_version
RUN curl -L https://github.com/saltstack/salt-bootstrap/releases/latest/download/bootstrap-salt.sh | sh -s -- -d -X -M -N stable ${salt_version}
ENTRYPOINT [ "/usr/bin/salt-master" ]
CMD [ "-l", "info" ]
