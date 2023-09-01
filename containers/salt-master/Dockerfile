FROM photon:3.0
ARG plugin_name
ARG salt_version
COPY ./eapi_plugin/files/$plugin_name $plugin_name
RUN tdnf update -y
RUN tdnf install -y salt3-master-$salt_version python3-pip python3-setproctitle
RUN pip3 install pyjwt
RUN pip3 install /$plugin_name
RUN rm SSEAPE*.whl
ENTRYPOINT [ "/usr/bin/salt-master" ]
CMD [ "-l", "info" ]