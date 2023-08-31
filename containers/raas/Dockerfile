FROM quay.io/centos/centos:stream9
ARG filename
COPY ./eapi_service/files/$filename $filename
COPY ./init.sh /usr/local/bin/init.sh
COPY ./eapi_service/files/sample-resource-types.raas /tmp/sample-resource-types.raas
RUN yum update -y
RUN yum install -y /$filename
RUN rm raas*.rpm
RUN chmod 755 /usr/local/bin/init.sh
USER raas
ENTRYPOINT ["/usr/local/bin/init.sh"]
CMD ["-l", "info"]
