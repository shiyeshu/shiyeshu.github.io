---
title: "php笔记--登陆验证和curl"
date: "2018-07-14T19:44:00+08:00"
lastmod: "2021-05-17T16:27:26+08:00"
description: "登录验证12345678910111213141516171819202122232425262728293031323334<?php include \"config/config.php\";$name = $_POST['name'];//post获得用户名表单值 $passowrd = $_P"
url: "/2018/07/14/php笔记--登陆验证和curl/"
slug: "php-bi-ji-deng-lu-yan-zheng-he-curl"
author: sshuo
source: html-legacy
commentsPath: "/2018/07/14/php笔记--登陆验证和curl/"
---

## 登录验证

```
<?php  
include "config/config.php";

$name = $_POST['name'];//post获得用户名表单值
    $passowrd = $_POST['password'];//post获得用户密码单值

    if ($name && $passowrd){//如果用户名和密码都不为空
             $sql = "select * from user where name = '$name' and password='$passowrd'";//检测数据库是否有对应的username和password的sql
             $result = mysqli_query($conn,$sql);//执行sql
             @$rows=mysqli_num_rows($result);//返回一个数值
             if($rows){//0 false 1 true
             	session_start();
	$_SESSION['username'] = $name;
                   header("refresh:0;url=admin/index.php");//如果成功跳转至welcome.html页面
                   exit;
             }else{
                echo "用户名或密码错误";
                echo "
                    <script>
                            setTimeout(function(){window.location.href='login.php';},1000);
                    </script>

                ";//如果错误使用js 1秒后跳转到登录页面重试;
             }

    }else{//如果用户名或密码有空
                echo "表单填写不完整";
                echo "
                      <script>
                            setTimeout(function(){window.location.href='login.php';},1000);
                      </script>";

                        //如果错误使用js 1秒后跳转到登录页面重试;
    }`
```

```
## 权限认证
```

```
		session_start();
if (!isset($_SESSION['username'])) {

echo "<script>window.location.href='../login.php';</script>";
}
?>
```

```
## CURL
```

```
$ch = curl_init();//起手式
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
$a= curl_exec($ch);//获取输出内容
curl_close($ch);//收工
echo "$a";输出内容
```
