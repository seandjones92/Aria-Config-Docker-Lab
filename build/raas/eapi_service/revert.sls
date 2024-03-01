revert_all:

  service.dead:
    - name: raas

  pkg.removed:
    - pkgs:
      - raas

  file.absent:
    - names:
      - /var/cache/salt/minion/SSEAPE/
      - /opt/saltstack/raas

  cmd.run:
    - name: systemctl daemon-reload
