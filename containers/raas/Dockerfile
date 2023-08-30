FROM quay.io/centos/centos:stream9
ARG filename
COPY ./eapi_service/files/$filename $filename
RUN yum update -y
RUN yum install -y /$filename
RUN rm raas*.rpm
USER raas
ENTRYPOINT ["/usr/bin/raas"]
CMD ["-l", "info"]
