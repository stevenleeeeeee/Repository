```txt
.es(index=sys-ot*,timefield=@timestamp,q="not ip : xx.xx.xx.xx and loglevel : err").label('This week').lines(width=1,fill=5).color('#de773f'),
.es(offset=-168h,index=sys-others*,timefield=@timestamp ,q="not ip : xx.xx.xx.xx and loglevel : err").label('Last Week').lines(width=1,fill=1).color(#9d9087).legend(columns=2),
.es(index=sys-ot*,timefield=@timestamp ,q="not ip : xx.xx.xx.xx and loglevel : err").label('速率').lines(width=0.1,fill=2).color('red').derivative().legend(columns=3),
.es(index=sys-ot*,timefield=@timestamp ,q="not ip : xx.xx.xx.xx and loglevel : err").label('趋势').lines(width=5,fill=0).color('#ed1941').mvavg(20).legend(columns=4)
```