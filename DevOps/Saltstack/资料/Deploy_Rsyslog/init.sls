{%- set packages_upgrade = salt['pillar.get']('packages_upgrade', False) %}
{%- if packages_upgrade %}
{%- set pkg_install_or_latest = 'latest' %}
{%- else %}
{%- set pkg_install_or_latest = 'installed' %}
{%- endif %}

rsyslog:
  pkg.{{ pkg_install_or_latest }}:
    - pkgs:
      - rsyslog
  service.running:
    - enable: True
    - reload: False
  #     - watch:
  #       - file: /etc/rsyslog.conf
