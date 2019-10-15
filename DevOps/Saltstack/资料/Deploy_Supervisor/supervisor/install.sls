# -*- coding: utf-8 -*-
# vim: ft=sls

{% from "supervisor/map.jinja" import supervisor with context %}

supervisor-pkg:
  pkg.installed:
    - name: {{ supervisor.pkg }}
