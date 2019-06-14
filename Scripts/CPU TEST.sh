#!/bin/sh
clear
#CPU压测脚本
echo -e "\033[36;1m==============================
欢迎使用CEHU CPU压测脚本
本脚本将以计算圆周率的方
式对CPU进行压测并输出压
测前频率和压测后频率
=============================="
sleep 5s;
#安装压测所需数学计算器
yum install bc -y
rm cpuinfo.log
clear
#选择压测强度
read -p "请选择压测强度：(1.低 2.中 3.高 4.炸机)" howToFuckCPU

#开始压测
if [ "$howToFuckCPU" == 1 ];then
    #输出压测前频率
    echo 压测前CPU频率为： >> cpuinfo.log
    cat /proc/cpuinfo | grep -i "cpu mhz" >> cpuinfo.log
    #低强度压测
    echo -e "\033[31;1m压测开始！"
    sleep 2s;
    for((i=1;i<=5;i++))
    do
        #进行圆周率5000位计算
        echo -e "\033[36;1m正在以计算圆周率后\033[31;1m10000\033[36;1m位的方式压测CPU
        \033[31;1m第$i遍\033[36;1m
        请耐心等待！\033[0m"
        echo "scale=10000; 4*a(1)" | bc -l -q
        clear
    done
    #输出压测后CPU频率
    echo 压测后CPU频率为： >> cpuinfo.log
    cat /proc/cpuinfo | grep -i "cpu mhz" >> cpuinfo.log
    clear
    cat cpuinfo.log
elif [ "$howToFuckCPU" == 2 ];then
    #输出压测前频率
    echo 压测前CPU频率为： >> cpuinfo.log
    cat /proc/cpuinfo | grep -i "cpu mhz" >> cpuinfo.log
    #中强度压测
    echo -e "\033[31;1m压测开始！"
    sleep 2s;
    for((i=1;i<=10;i++))
    do
        #进行圆周率5000位计算
        echo -e "\033[36;1m正在以计算圆周率后\033[31;1m50000\033[36;1m位的方式压测CPU
        \033[31;1m第$i遍\033[36;1m
        请耐心等待！\033[0m"
        echo "scale=50000; 4*a(1)" | bc -l -q
        clear
    done
    #输出压测后CPU频率
    echo 压测后CPU频率为： >> cpuinfo.log
    cat /proc/cpuinfo | grep -i "cpu mhz" >> cpuinfo.log
    clear
    cat cpuinfo.log
elif [ "$howToFuckCPU" == 3 ];then
    #输出压测前频率
    echo 压测前CPU频率为： >> cpuinfo.log
    cat /proc/cpuinfo | grep -i "cpu mhz" >> cpuinfo.log
    #高强度压测
    echo -e "\033[31;1m压测开始！"
    sleep 2s;
    for((i=1;i<=15;i++))
    do
        echo -e "\033[36;1m正在以计算圆周率后\033[31;1m100000\033[36;1m位的方式压测CPU
        \033[31;1m第$i遍\033[36;1m
        请耐心等待！\033[0m"
        echo "scale=100000; 4*a(1)" | bc -l -q
        clear
    done
    #输出压测后CPU频率
    echo 压测后CPU频率为： >> cpuinfo.log
    cat /proc/cpuinfo | grep -i "cpu mhz" >> cpuinfo.log
    clear
    cat cpuinfo.log
elif [ "$howToFuckCPU" == 4 ];then
    #输出压测前频率
    echo 压测前CPU频率为： >> cpuinfo.log
    cat /proc/cpuinfo | grep -i "cpu mhz" >> cpuinfo.log
    #炸机
    echo -e "\033[31;1m炸机模式启动！如非超牛逼的CPU，请勿尝试！否则后果自负！
    (其实也就是死机，若按CTRL+C无法取消，重启即可。)\033[0m"
    sleep 3s;
    echo -e "\033[31;1m压测开始！"
    sleep 1s;
    for((i=1;i<=50;i++))
    do
        echo -e "\033[36;1m正在以计算圆周率后\033[31;1m1000000\033[36;1m位的方式压测CPU
        \033[31;1m第$i遍\033[36;1m
        请耐心等待！\033[0m"
        echo "scale=1000000; 4*a(1)" | bc -l -q
        clear
    done
    #输出压测后CPU频率
    echo 压测后CPU频率为： >> cpuinfo.log
    cat /proc/cpuinfo | grep -i "cpu mhz" >> cpuinfo.log
    clear
    cat cpuinfo.log
else
    echo -e "\033[31;1m输入错误！脚本终止，请重新运行！"
fi
