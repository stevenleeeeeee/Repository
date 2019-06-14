include:
  - .

/etc/rsyslog.d/server.conf:
  file.managed:
    - source: salt://rsyslog/conf/server.conf
    - user: root
    - group: root
    - dir_mode: 444
    - watch_in:
      - service: rsyslog
