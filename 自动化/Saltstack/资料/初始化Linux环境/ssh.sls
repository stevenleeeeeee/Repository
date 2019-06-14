sshd_config:
  file.managed:
    - name: /etc/ssh/sshd_config
    - source: salt://init/files/sshd_config.template
    - user: root
    - group: root
    - mode: 644
  service.running:
    - name: sshd
    - enable: True
    - reload: True
    - watch:
      - file: sshd_config
