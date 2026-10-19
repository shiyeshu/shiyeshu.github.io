---
title: "一个简易授权demo"
date: "2018-08-20T14:35:00+08:00"
lastmod: "2021-05-17T16:51:16+08:00"
description: "在页面中引用，比如： 1234567<?phpecho'1111';include ('shouquan.php');echo'1111';?> 授权操作 123456789101112131415161718192021222324252627282930313233343536373839404142434445464748495"
url: "/2018/08/20/一个简易授权demo/"
slug: "yi-ge-jian-yi-shou-quan-demo"
author: sshuo
source: html-legacy
commentsPath: "/2018/08/20/一个简易授权demo/"
---

在页面中引用，比如：

```
<?php

echo'1111';
include ('shouquan.php');
echo'1111';

?>
```

```
授权操作
```

```
$url=$_SERVER['SERVER_NAME'];

include ('key.php');
    $curl = curl_init();
    //设置抓取的url
    curl_setopt($curl, CURLOPT_URL, 'http://localhost/api/api.php');
    //设置头文件的信息作为数据流输出
    curl_setopt($curl, CURLOPT_HEADER, 0);
    //设置获取的信息以文件流的形式返回，而不是直接输出。
    curl_setopt($curl, CURLOPT_RETURNTRANSFER, 1);
    //设置post方式提交
    curl_setopt($curl, CURLOPT_POST, 1);
    //设置post数据
    $post_data = array(
        "domain" => "$url",
        "key" => "$key"
        );
    curl_setopt($curl, CURLOPT_POSTFIELDS, $post_data);
    //执行命令
    $data = curl_exec($curl);
    //关闭URL请求
    curl_close($curl);

//echo "$data";
if ($data=='true') {
echo	'域名验证成功！<br>';
} else {
	exit();
}`</pre>

key文件，用于存储激活码、授权码
<pre>`<?php
$key='123456';//输入激活码
?>`</pre>

api文件，接受客户端post请求并返回相应数据
<pre>`<?php
$api=$_POST['key'];
$domain=$_POST['domain'];

$servername = "localhost";
$username = "root";
$password = "root";
$dbname = "selectdata";

// 创建连接
$conn = new mysqli($servername, $username, $password, $dbname);
// Check connection
if ($conn->connect_error) {
    die("连接失败: " . $conn->connect_error);
} 

$rs = mysqli_query($conn,"SELECT * FROM data WHERE domain='$domain'");
$aa=mysqli_fetch_array($rs);

if ($api==$aa[1]) {
	echo'true';
} else {
	echo'false';
}
```

```
将程序重要函数/操作/行为添加到shouquan.php中并对其加密混淆，以达到防破解的目的

嗯...暂时就想到这么多。

2018.12.1

客户端代码
```

````
<?php
 //获取不带端口号的域名前缀
 $servername = trim($_SERVER['SERVER_NAME']);
 //获取服务端授权文件校验
 $verifyurl = file_get_contents('http://www.toyean.com/zb_users/upload/copyright.php?domain='.$servername);
 if(!empty($verifyurl)){
 	echo "已授权！";    //授权成功
 }else{
 	die("未授权！");    //授权失败
 }
 ?>```

 服务端代码

 ```<?php</span>
 <pre>`//获取域名
 $domain = $_GET['domain'];
 //授权域名列表
 $Array = array('127.0.0.1','localhost');
 //校验结果
 echo in_array($domain, $Array) ? 'yes' : '';
 ?>
````

感谢[@慕若曦](muruoxi.com)的指点
