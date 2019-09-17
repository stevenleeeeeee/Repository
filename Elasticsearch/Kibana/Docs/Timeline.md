#### Timelion时间序列数据可视化工具介绍
```txt
在可视化中组合完全独立的数据源，检索时间序列书籍、通过计算挑选复杂问题的答案展示可视化结果

    每个唯一的用户在一段时间内查看了多少次页面
    本周*与上周*间流量的区别
    今天日本有多少百分比的人口访问本网站
    标准普尔500指数的10天移动均线是什么
    过去*年内收到的所有搜索请求的和

```
#### 历史
```txt
.es(index=sys-ot*,timefield=@timestamp,q="not ip : xx.xx.xx.xx and loglevel : err").label('This week').lines(width=1,fill=5).color('#de773f'),
.es(offset=-168h,index=sys-others*,timefield=@timestamp ,q="not ip : xx.xx.xx.xx and loglevel : err").label('Last Week').lines(width=1,fill=1).color(#9d9087).legend(columns=2),
.es(index=sys-ot*,timefield=@timestamp ,q="not ip : xx.xx.xx.xx and loglevel : err").label('速率').lines(width=0.1,fill=2).color('red').derivative().legend(columns=3),
.es(index=sys-ot*,timefield=@timestamp ,q="not ip : xx.xx.xx.xx and loglevel : err").label('趋势').lines(width=5,fill=0).color('#ed1941').mvavg(20).legend(columns=4)

title()
lines()
label()
color()     颜色
legend()
derivative()
mvavg()     使用制定数量的采样点进行计算给定时间窗口的移动平均值，这对于分析有很多噪音数据的时序图非常有帮助   
```