---
title: "搭建一个私人网盘--cloudreve"
date: "2018-08-05T21:48:00+08:00"
lastmod: "2021-05-17T16:33:48+08:00"
description: "万恶的度盘限速实在厉害，用了插件突破结果账号被限速了。 今天给大家推荐一款私人云盘cloudreve官网http://cloudreve.org/ 优点云存储填写简单信息即可快速对接七牛、又拍云、阿里云OSS、AWS S3，当然你也可以选择将文件存放在本地。 多用户你可以将Cloudreve作为私有云使用，Cloudreve强大的用户系统也可作为公有云平台使用。 上传策略不同用户组可绑定不同上传策"
url: "/2018/08/05/搭建一个私人网盘--cloudreve/"
slug: "da-jian-yi-ge-si-ren-wang-pan-cloudreve"
author: sshuo
source: html-legacy
commentsPath: "/2018/08/05/搭建一个私人网盘--cloudreve/"
---

万恶的度盘限速实在厉害，用了插件突破结果账号被限速了。

今天给大家推荐一款私人云盘cloudreve  
官网[http://cloudreve.org/](http://cloudreve.org/)

## 优点

### 云存储

填写简单信息即可快速对接七牛、又拍云、阿里云OSS、AWS S3，当然你也可以选择将文件存放在本地。

### 多用户

你可以将Cloudreve作为私有云使用，Cloudreve强大的用户系统也可作为公有云平台使用。

### 上传策略

不同用户组可绑定不同上传策略，并在多个上传策略间快速切换，充分利用存储资源。

### 在线预览

支持图片、视频、音频、Office文档在线预览；文本文件、Markdown文件在线编辑。

### 文件分享

用户可以创建私有或公有分享链接，快速分享文件、目录给好友。

### WebDAV支持

你可以将网盘映射到本地管理，或者使用其他支持WebDAV协议的文件管理器，实现无缝跨平台。

### 响应式布局

全站响应式布局，移动端也能拥有良好的使用体验

### 文件上传

支持大文件分片上传、断点续传、批量上传、拖拽上传。

### 易于部署

使用PHP + MySQL架构，简单5分钟即可成功部署您的专属云盘。

以上是我从官网复制过来的（逃~

## 安装步骤：

有两种安装方式

## 一、通过Composer安装

1. 安装Composer

   ```
   `curl -sS https://getcomposer.org/installer | php
   mv composer.phar /usr/local/bin/composer`
   ```

### 2. 使用Composer安装Cloudreve

#安装开发版

`$ composer create-project hfo4/cloudreve:dev-master`

#出现如下提示表示安装完成  
Congratulations! Cloudreve has been installed successfully.

Here’s some informatioin about yor Cloudreve:  
Homepage: [https://pan.aoaoao.me/](https://pan.aoaoao.me/)  
Admin Panel: [https://pan.aoaoao.me/Admin](https://pan.aoaoao.me/Admin)  
Default username: [admin@cloudreve.org](mailto:admin@cloudreve.org)  
Default password: admin

\[v\_blue\]runtime目录需要写入权限，如果你使用本地存储，public 目录也需要有写入权限\[/v\_blue\]

## 常规安装（虚拟主机安装）

在官网下载程序包并解压到目录  
官方下载地址：[http://cloudreve.org/download.php](http://cloudreve.org/download.php)

将根目录下的mysql.sql到入到你的数据库，编辑application/database\_sample.php文件，填写数据库信息，并重命名为database.php  
正常访问即可  
后台：abc.com/admin/  
默认账号: [admin@cloudreve.org](mailto:admin@cloudreve.org)  
默认密码: admin

登录后可在管理面板中添加管理员  
[![](/images/2018/08/2018080513220314.png)](/images/2018/08/2018080513220314.png)  
[![](/images/2018/08/2018080513225022.png)](/images/2018/08/2018080513225022.png)

如果想作为私人网盘使用也可以在管理面板中设置  
[![](/images/2018/08/2018080513283574.png)](/images/2018/08/2018080513283574.png)

提示：  
要记得设置用户空间大小，默认为1G  
要记得设置文本编辑大小限制，不然大点的文本会不能编辑  
360急速浏览器自带下载功能下载时可能会异常  
离线下载功能需要aria2支持。详细配置教程[点击此处](https://github.com/HFO4/Cloudreve/wiki/%E7%A6%BB%E7%BA%BF%E4%B8%8B%E8%BD%BD%E5%AF%B9%E6%8E%A5%E8%AF%B4%E6%98%8E)  
官方项目地址：[点击此处](https://github.com/HFO4/Cloudreve/)
