FROM almalinux:9.4-20240923
ARG plugin_name
ARG salt_version
COPY ./eapi_plugin/files/$plugin_name /$plugin_name
RUN curl -L https://github.com/saltstack/salt-bootstrap/releases/latest/download/bootstrap-salt.sh | sh -s -- -d -X -M -N stable ${salt_version}
RUN salt-pip install /$plugin_name
RUN rm SSEAPE*.whl
ENTRYPOINT [ "/usr/bin/salt-master" ]
CMD [ "-l", "info" ]
