---
title: "又见卡死图，竟然一个“小黑点”就能干掉QQ？（首发FREEBUF）"
date: "2018-05-17T15:46:00+08:00"
lastmod: "2021-05-17T16:24:07+08:00"
description: "前一阵子QQ群里流行了一个东西，一段话加上一个黑点（表情），点击之后QQ就会卡死。 当时只觉得很好玩，没多久就又见了一次。 既然又看到了就一定要好好看看了。 刚开始遇到这个时第一反应是曾经看过的文章《一张GIF引发的微信崩溃》，所以第一反应也是扔进010Editor看看，然而并没有什么异常的地方。就在这时无意间看到了图片的名字，觉得不一般，后想了想会不会是和“十五个句号”一样触发了什么东西。"
url: "/2018/05/17/又见卡死图，竟然一个“小黑点”就能干掉QQ？/"
slug: "you-jian-ka-si-tu-jing-ran-yi-ge-xiao-hei-dian-jiu-neng-gan-diao-qq-shou-fa-free"
author: sshuo
source: html-legacy
commentsPath: "/2018/05/17/又见卡死图，竟然一个“小黑点”就能干掉QQ？/"
categories: ["网络安全"]
tags: ["恶意代码", "漏洞复现"]
---

**前一阵子QQ群里流行了一个东西，一段话加上一个黑点（表情），点击之后QQ就会卡死。**

[![1.jpg](http://image.3001.net/images/20180510/15259586086872.jpg!small)](http://image.3001.net/images/20180510/15259586086872.jpg)

当时只觉得很好玩，没多久就又见了一次。

[![2.png](http://image.3001.net/images/20180510/1525958628702.png!small)](http://image.3001.net/images/20180510/1525958628702.png)

既然又看到了就一定要好好看看了。

刚开始遇到这个时第一反应是曾经看过的文章[《一张GIF引发的微信崩溃》](http://www.freebuf.com/articles/terminal/135577.html)，所以第一反应也是扔进010Editor看看，然而并没有什么异常的地方。就在这时无意间看到了图片的名字，觉得不一般，后想了想会不会是和“十五个句号”一样触发了什么东西。

表情图片名称：

![3.png](http://image.3001.net/images/20180510/1525958721638.png!small)![4.png](http://image.3001.net/images/20180510/15259587252029.png!small)![5.png](http://image.3001.net/images/20180510/15259587284183.png!small)

最后看了看实在想不到有什么异常的。虽然名字奇怪了点但一般这种图片不都是这样吗。更何况都有后缀名结尾，应该是翻不起什么浪的。这一会的我怕是已经有点草木皆兵了。

如果不是图片的话那么就是文字的原因喽？文字复制~

![6.jpg](http://image.3001.net/images/20180510/15259587592605.jpg!small)

浏览器顺利爆炸：

![7.png](http://image.3001.net/images/20180510/15259587684833.png!small)

地址栏里好像有什么东西。经过精简最后拿到了：%E2%80%8E

浏览器中重复出现这个东西：

![8.png](http://image.3001.net/images/20180510/15259587821030.png!small)

到这里真相就差不多了，N多个%E2%80%8E循环出现。那么这个%E2%80%8E到底是什么呢个？经过查阅资料这东西叫ZERO-WIDTH SPACE，顾名思义0宽度，所以这东西看不见。那么既然是“隐形”的那它隐藏了什么？编码转换后得到如下：

![9.png](http://image.3001.net/images/20180510/15259588195995.png!small)

我们可以看出这三个起来作用“&amp;#8206;&amp;#8207;&amp;#8235;”

> &amp;#8206;LRM‎ 从左到右标记
> &amp;#8207;RLM从右向左标记
> &amp;#8235;RLE‫ 开始从右向左嵌入

到这里就可以看出了，其实&amp;#8235也是可以去掉的，真正生效的是LRM和RLM。多个左右标记循环出现，当用户去指定一个位置时会因为“反复横跳”导致当前程序崩溃。而原来的黑点以及国旗只是给用户错觉，让人以为是它的原因。而“&amp;#8206;&amp;#8207;&amp;#8235;”重复出现应该也只是制造者为了尽量卡死用户而特意重复书写，并不是因为某种原因而生成的。理论上来说这个对所有触屏手机和其运行的软件能够生效。（如果点一次没卡可以多作几次，iOS未测试）。

那么既然知道了原理我们也可以制作一个自己的“卡死图”。

```
格式基本为：（&<span class="hljs-selector-id">#8206</span>;&<span class="hljs-selector-id">#8207</span>;）*<span class="hljs-selector-tag">N</span>+图片或文字
```

然后将（&amp;#8206;&amp;#8207;）\*N由unicode转换为ASCII，得到的即为只显示文字或图片的“卡死图”。

原聊天记录中的代码（未保存图片）。

链接: [https://pan.baidu.com/s/1VRss3DSb79WFfydY4Vh7YQ](https://pan.baidu.com/s/1VRss3DSb79WFfydY4Vh7YQ) 密码: v5qt

## 查阅资料

> [《一个特殊的字符？（%E2%80%8B）》](https://blog.csdn.net/u014271114/article/details/55668115)
> [《\[BUG随想录\] 看不见的分隔符:Zero-width space》](https://www.cnblogs.com/SivilTaram/p/5767450.html)

emmmmm….虽然是自己的东西但还是放个原文链接吧

[http://www.freebuf.com/articles/system/171435.html](http://www.freebuf.com/articles/system/171435.html)
