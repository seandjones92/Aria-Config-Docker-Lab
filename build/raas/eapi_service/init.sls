{#
  Salt State to Install and Configure Aria Automation Config Service "raas"
#}

{% set sse_pg_endpoint = salt['pillar.get']('sse_pg_endpoint', "localhost") %}
{% set sse_pg_port = salt['pillar.get']('sse_pg_port', "5432") %}

{% set sse_pg_username = salt['pillar.get']('sse_pg_username', "salt_eapi") %}
{% set sse_pg_password = salt['pillar.get']('sse_pg_password', "abc123") %}

{% set sse_redis_endpoint = salt['pillar.get']('sse_redis_endpoint', "localhost") %}
{% set sse_redis_port = salt['pillar.get']('sse_redis_port', "6379") %}
{% set sse_redis_username = salt['pillar.get']('sse_redis_username', "salt_eapi") %}
{% set sse_redis_password = salt['pillar.get']('sse_redis_password', "abc123") %}

{% set sse_eapi_username = salt['pillar.get']('sse_eapi_username', "root") %}
{% set sse_eapi_password = salt['pillar.get']('sse_eapi_password', "salt") %}

{% set sse_eapi_key = salt['pillar.get']('sse_eapi_key', "auto") %}

{% if salt['sdb.get']('sdb://osenv/SSE_CERT_CN') and salt['sdb.get']('sdb://osenv/SSE_CERT_CN') != 'sdb://osenv/SSE_CERT_CN' %}
{% set sse_eapi_server_cert_cn = salt['sdb.get']('sdb://osenv/SSE_CERT_CN') %}
{% set sse_eapi_server_cert_name = sse_eapi_server_cert_cn %}
{% else %}
{% set sse_eapi_server_cert_cn = salt['pillar.get']('sse_eapi_server_cert_cn', 'localhost') %}
{% set sse_eapi_server_cert_name = salt['pillar.get']('sse_eapi_server_cert_name', 'localhost') %}
{% endif %}
{% set sse_eapi_cert = "/etc/pki/raas/certs/"+sse_eapi_server_cert_name+".crt" %}
{% set sse_eapi_certkey = "/etc/pki/raas/certs/"+sse_eapi_server_cert_name+".key" %}

{% set sse_eapi_ssl_enabled = salt['pillar.get']('sse_eapi_ssl_enabled', True) %}
{% if sse_eapi_ssl_enabled %}
{% set http_prefix = "https://" %}
{% else %}
{% set http_prefix = "http://" %}
{% endif %}

{% set sse_customer_id = salt['pillar.get']('sse_customer_id', '43cab1f4-de60-4ab1-85b5-1d883c5c5d09') %}

{% set cachedir = opts['cachedir'] + "/SSEAPE/" %}

install_xmlsec:
  pkg.installed:
    - sources:
      - openssl: salt://{{ slspath }}/files/openssl-3.0.1-47.el9_1.x86_64.rpm
      - openssl-libs: salt://{{ slspath }}/files/openssl-libs-3.0.1-47.el9_1.x86_64.rpm
      - xmlsec1: salt://{{ slspath }}/files/xmlsec1-1.2.29-9.el9.x86_64.rpm
      - xmlsec1-openssl: salt://{{ slspath }}/files/xmlsec1-openssl-1.2.29-9.el9.x86_64.rpm
      - libxslt: salt://{{ slspath }}/files/libxslt-1.1.34-9.el9.x86_64.rpm
      - libtool-ltdl: salt://{{ slspath }}/files/libtool-ltdl-2.4.6-45.el9.x86_64.rpm
      - singleton-manager-i18n: salt://{{ slspath }}/files/singleton-manager-i18n-0.6.13-0.el7.x86_64.rpm
      - ssc-translation-bundle: salt://{{ slspath }}/files/ssc-translation-bundle-8.13.1-1.ph3.noarch.rpm

install_raas:
  pkg.installed:
    - sources:
      - raas: salt://{{ slspath }}/files/raas-8.13.1.4.el9.x86_64.rpm

  cmd.run:
    - name: systemctl daemon-reload
    - onchanges:
      - pkg: install_raas

create_pki_raas_path_eapi:
  file.directory:
    - name: /etc/pki/raas/certs
    - makedirs: True
    - dir_mode: 755

create_ssl_certificate_eapi:
  module.run:
    - name: tls.create_self_signed_cert
    - CN: {{ sse_eapi_server_cert_cn }}
    - cert_filename: {{ sse_eapi_server_cert_name }}
    - tls_dir: raas
    - require:
      - file: create_pki_raas_path_eapi
    - onchanges:
      - pkg: install_raas

set_certificate_permissions_eapi:
  file.managed:
    - name: {{ sse_eapi_cert }}
    - user: raas
    - group: raas
    - mode: 400
    - replace: False
    - create: False

set_key_permissions_eapi:
  file.managed:
    - name: {{ sse_eapi_certkey }}
    - user: raas
    - group: raas
    - mode: 400
    - replace: False
    - create: False

raas_owns_raas:
  file.directory:
    - name: /etc/raas/
    - user: raas
    - group: raas
    - dir_mode: 750

configure_raas:
  file.managed:
    - name: /etc/raas/raas
    - source: salt://{{ slspath }}/files/raas.jinja
    - template: jinja
    - user: raas
    - group: raas
    - mode: 660
    - context:
        sse_customer_id: {{ sse_customer_id }}
        sse_eapi_ssl_enabled: {{ sse_eapi_ssl_enabled }}
        sse_pg_endpoint: {{ sse_pg_endpoint }}
        sse_pg_port: {{ sse_pg_port }}
        sse_pg_username: {{ sse_pg_username }}
        sse_pg_password: {{ sse_pg_password }}
        sse_redis_endpoint: {{ sse_redis_endpoint }}
        sse_redis_port: {{ sse_redis_port }}
        sse_redis_username: {{ sse_redis_username }}
        sse_redis_password: {{ sse_redis_password }}
        sse_eapi_certkey: {{ sse_eapi_certkey }}
        sse_eapi_cert: {{ sse_eapi_cert }}
    - require:
      - pkg: install_raas

save_credentials:
  cmd.run:
    - require:
      - file: raas_owns_raas
      - file: configure_raas
{% if not salt['file.file_exists']('/etc/raas/pki/.raas.key') and sse_eapi_key != "auto" %}
      - cmd: set_raas_key
{% endif %}
    - runas: raas
    - names:
      - "/usr/bin/raas save_creds
            'postgres={\"username\":\"{{ sse_pg_username }}\",\"password\":\"{{ sse_pg_password }}\"}'
            'redis={\"password\":\"{{ sse_redis_password }}\"}'"
    - creates:
      - /etc/raas/raas.secconf

set_secconf_permissions:
  file.managed:
    - name: /etc/raas/raas.secconf
    - user: raas
    - group: raas
    - mode: 600
    - create: False
    - replace: False
    - require:
      - cmd: save_credentials

ensure_raas_pki_directory:
  file.directory:
    - name: /etc/raas/pki
    - user: raas
    - group: raas
    - dir_mode: 700

{% if not salt['file.file_exists']('/etc/raas/pki/.raas.key') and sse_eapi_key != "auto" %}
set_raas_key:
  cmd.run:
    - name: echo "${RAAS_KEY}" > /etc/raas/pki/.raas.key
    - env:
        RAAS_KEY: '{"priv": "{{ sse_eapi_key }}"}'
    - require:
      - file: ensure_raas_pki_directory
{% endif %}

change_owner_to_raas:
  file.directory:
    - name: /etc/raas/pki
    - user: raas
    - group: raas
    - dir_mode: 700
    - recurse:
      - user
      - group
      - mode

/usr/sbin/ldconfig:
  cmd.run

start_raas:
  service.running:
    - name: raas
    - enable: True
    - require:
      - pkg: install_raas
    - watch:
      - file: configure_raas
    - check_cmd:
      - "until curl -k {{ http_prefix }}localhost/version > /dev/null 2>&1; do sleep 2 && ((x++)); if [[ x -eq 30 ]]; then break; fi; done"

# Under certain conditions, such as initial provisioning of the raas database with multiple raas heads,
# the raas process may need to wait for the initial raas head to complete database initialization.
# In this case, we will restart raas after a delay.  The raas head that initializes the database will
# also import the default set of objects.  Which does not need to be repeated.
restart_raas_and_confirm_connectivity:
  cmd.run:
    - names:
      - "salt-call service.restart raas"
    - check_cmd:
      - "until curl -k {{ http_prefix }}localhost/version > /dev/null 2>&1; do sleep 2 && ((x++)); if [[ x -eq 30 ]]; then break; fi; done"
    - unless:
      - "curl -k
              -c {{ cachedir }}eapi_cookie.txt
              -u {{ sse_eapi_username }}:{{ sse_eapi_password }} '{{ http_prefix }}localhost/version' >/dev/null"

get_initial_objects_file:
  file.managed:
    - name: /tmp/sample-resource-types.raas
    - source: salt://{{ slspath }}/files/sample-resource-types.raas
    - user: raas
    - group: raas
    - mode: 0640


import_initial_objects:
  cmd.run:
    - runas: raas
    - names:
      - "/usr/bin/raas dump --insecure --server {{ http_prefix }}127.0.0.1 --auth {{ sse_eapi_username }}:{{ sse_eapi_password }} --mode import < /tmp/sample-resource-types.raas"

raas_service_restart:
  cmd.run:
    - names:
      - "systemctl restart raas"
