/etc/rsyslog.d/test.conf:
  file.managed:
    - source: salt://files/test.tmpl
    - mode: 644
    - template: jinja
    - defaults:
        ADDRESS: {{ grains['id'] }}
        KAFKA_ADDRESS: 192.168.70.129:9200

rsyslog-install:
  pkg.installed:
    - pkgs:
      - rsyslog
      - rsyslog-mmjsonparse
      - rsyslog-kafka
      - rsyslog-elasticsearch

running-rsyslog:
  service.running:
    - name: rsyslog
    - enable: true
    - reload: true
    - watch:
      - pkg: rsyslog-install
      - file: /etc/rsyslog.d/test.conf
      