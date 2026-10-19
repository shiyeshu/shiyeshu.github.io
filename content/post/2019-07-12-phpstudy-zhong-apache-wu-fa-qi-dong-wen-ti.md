---
title: "phpstudy中Apache无法启动问题"
date: "2019-07-12T19:55:00+08:00"
lastmod: "2021-05-17T17:25:23+08:00"
description: "使用phpstudy时其中Apache无法启动，点击启动后再次自动关闭 在网上查了很多资料，有的说是端口占用、有的说是程序冲突 也有说vhost出错的，当然这几个确实可能导致这种问题 但是最后解决却是在httpd.conf中 进入到Apache的目录中手动用cmd启动 查看报错文件信息httpd.conf第223行 文件在Apache\\conf\\下 . 第223行路径最后多了一个“\\”，去掉以"
url: "/2019/07/12/phpstudy中Apache无法启动问题/"
slug: "phpstudy-zhong-apache-wu-fa-qi-dong-wen-ti"
author: sshuo
source: html-legacy
commentsPath: "/2019/07/12/phpstudy中Apache无法启动问题/"
---

使用phpstudy时其中Apache无法启动，点击启动后再次自动关闭

![](/images/2019/07/527146839.gif)

在网上查了很多资料，有的说是端口占用、有的说是程序冲突

也有说vhost出错的，当然这几个确实可能导致这种问题

但是最后解决却是在httpd.conf中

进入到Apache的目录中手动用cmd启动

![](/images/2019/07/2178250370.png)

查看报错文件信息httpd.conf第223行

文件在Apache\\conf\\下

.![](/images/2019/07/571318206.png)

第223行路径最后多了一个“\\”，去掉以后再重新启动Apache。现在服务已经可以正常启动了

最后提一下，这个问题往往由于更换web目录时偷懒造成的。

![](/images/2019/07/2874291778.png)

正常操作是点击“打开”选择路径然后应用，但是偷懒的人会直接在前面的路径框里修改然后应用，这个时候往往会在路径最后留上一个\\，于是就报错了
