---
title: "快速搭建一个KMS服务器"
date: "2018-08-04T16:54:00+08:00"
lastmod: "2021-05-17T16:32:09+08:00"
description: "KMS用来激活 VOL 版本的 Windows 和 Office。经常能在网上看到有人提供的 KMS 服务器地址，那么你有没有想过自己也来搞一个这样的服务呢？最近看到了大佬的一键脚本点击查看于是写篇文章水一下。以祭我这长了蜘蛛网的博客。 root登录服务器复制粘贴以下命令并回车 1wget --no-check-certificate https://github.com&#"
url: "/2018/08/04/快速搭建一个KMS服务器/"
slug: "kuai-su-da-jian-yi-ge-kms-fu-wu-qi"
author: sshuo
source: html-legacy
commentsPath: "/2018/08/04/快速搭建一个KMS服务器/"
categories: ["开发项目"]
tags: ["服务器", "运维", "Windows"]
---

KMS用来激活 VOL 版本的 Windows 和 Office。经常能在网上看到有人提供的 KMS 服务器地址，那么你有没有想过自己也来搞一个这样的服务呢？最近看到了大佬的一键脚本[点击查看](https://teddysun.com/530.html)于是写篇文章水一下。以祭我这长了蜘蛛网的博客。

root登录服务器复制粘贴以下命令并回车

```
wget --no-check-certificate https://github.com/teddysun/across/raw/master/kms.sh && chmod +x kms.sh && ./kms.sh
```

安装完成后执行以下命令查看端口状态（一般都没啥问题）

```
netstat -nxtlp | grep 1688
```

[![](/images/2018/08/2018080408464186.png)](/images/2018/08/2018080408464186.png)  
本脚本安装完成后，会将 KMS 服务加入开机自启动

查看运行状态

[![](/images/2018/08/2018080408424115.png)](/images/2018/08/2018080408424115.png)

使用方法  
win  
管理员身份运行cmd或新建bat文件输入以下内容

/d "%SystemRoot%\\system32"

```
slmgr /skms 你的VPS的IP或者绑定的域名
slmgr /ato
slmgr /xpr
```

office  
同上，命令如下

/d "%ProgramFiles%\\Microsoft Office\\Office15"

```
#依次执行下面的命令
cscript ospp.vbs /sethst:你的VPS的IP或者绑定的域名
cscript ospp.vbs /act
cscript ospp.vbs /dstatus
```

常用命令

```
启动：/etc/init.d/kms start
停止：/etc/init.d/kms stop
重启：/etc/init.d/kms restart
状态：/etc/init.d/kms status
卸载：./kms.sh uninstall
```

提示：KMS方式激活是有时间限制的，本文章仅供娱乐
