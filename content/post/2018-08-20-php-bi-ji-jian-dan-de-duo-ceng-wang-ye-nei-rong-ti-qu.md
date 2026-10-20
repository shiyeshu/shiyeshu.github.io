---
title: "php笔记---简单的多层网页内容提取"
date: "2018-08-20T14:15:00+08:00"
lastmod: "2021-05-17T16:46:35+08:00"
description: "举例 求手机号177xxxx6832完整号码 以河南驻马店为例，找出相应号段 http://www.bixinshui.com/city/279 177号段 单号段网页内容 开始程序 1234567891011121314151617181920212223242526272829303132333435363738394041424344454647创建数组$arr = a"
url: "/2018/08/20/php笔记---简单的多层网页内容提取/"
slug: "php-bi-ji-jian-dan-de-duo-ceng-wang-ye-nei-rong-ti-qu"
author: sshuo
source: html-legacy
commentsPath: "/2018/08/20/php笔记---简单的多层网页内容提取/"
categories: ["开发项目"]
---

举例

求手机号177xxxx6832完整号码

以河南驻马店为例，找出相应号段 [http://www.bixinshui.com/city/279](http://www.bixinshui.com/city/279)

177号段![](/images/2018/09/1697048414.png)

单号段网页内容

![](/images/2018/09/392574615.png)

开始程序

```
创建数组
$arr = array('1773965','1776026','1776027','1776025','1776021','1776022','1776023','1774941','1774697','1773964','1773969','1773968','1773966','1773967','1773953','1773948','1773738','1773702','1771919','1771917','1771918','1771916','1770396','1770397','1779655','1779661','1779656','1779657','1779654','1771914','1774044');`</pre>

通过遍历数组获取所有单号段网页内容
<pre>`创建CURL操作

$url = "";//目标网页url
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
      $response= curl_exec($ch);
        curl_close($ch);
preg_match_all("/<td>\n\d{7}6832<\/td>/",$response, $a);//通过正则提取特定结尾号码
$shuzu=$a[0];        

echo "$shuzu[0]";

echo "<br>";`</pre>

使用foreach
<pre>`foreach($arr as $value){ 
}`</pre>

完整成品
<pre>`<?php
$arr = array('1773965','1776026','1776027','1776025','1776021','1776022','1776023','1774941','1774697','1773964','1773969','1773968','1773966','1773967','1773953','1773948','1773738','1773702','1771919','1771917','1771918','1771916','1770396','1770397','1779655','1779661','1779656','1779657','1779654','1771914','1774044');
foreach($arr as $value){ 

$url = "http://www.bixinshui.com/phone/$value";
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);

        $response= curl_exec($ch);
        curl_close($ch);
preg_match_all("/<td>\n\d{7}<span style="font-size: 1em;">6832<span style="font-size: 1em;"><\/td>/",$response, $a);
$out=$a[0];        

echo "$out[0]";

echo "<br>";

}</span></span>
```
