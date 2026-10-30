---
title: "php2shell 在野利用机制与蜜罐捕获深度复盘"
date: 2026-10-30T23:45:00+08:00
lastmod: 2026-10-30T23:45:00+08:00
description: "2026 年 10 月 PHP 官方修复 php2shell（CVE-2026-109618 / CVE-2026-109619）后，我自建的蜜罐在漏洞披露 4 天后捕获到 81 秒内 20 次重放的在野堆塑形探测。本文结合第一手流量日志，拆解 Zend 引擎 OOM/longjmp 状态倒挂机理、样本堆风水细节，以及 AI 参与攻防的观察。"
url: "/2026/10/30/php2shell-honeypot-forensics/"
slug: "php2shell-honeypot-forensics"
author: sshuo
categories: ["网络安全"]
tags: ["PHP", "漏洞分析", "蜜罐", "在野利用"]
draft: false
---
2026 年 10 月 21 日，PHP 官方正式发布了 8.5.12、8.4.27、8.3.36 与 8.2.35 多个分支的安全补丁，修复了被统称为 **php2shell** 的两个关键漏洞：**CVE-2026-109618** 与 **CVE-2026-109619**（CVSS v4.0 9.2，影响自 PHP 5.4 引入上传进度跟踪机制以来的所有版本）。

披露仅 4 天后，我部署的低交互高捕获蜜罐就精准记录到了一组高度吻合的在野探测：同一 IP 在 81 秒内重放了 20 次请求体完全一致的 POST。单请求包含 203 个 Form-Data Part、填充 4,000 字节的自定义会话键名、200 个 256 字节的 spray 分块，以及一个直接被命名为 `uaf` 的 4,608 字节二进制块。

整个攻击过程**没有任何 PHP 标签，没有上传 webshell，也未发起任何 LFI 文件包含**——这是一起纯粹针对 Zend MM 内存排布的堆塑形探测。

更具戏剧性的是，在这个漏洞从预警到捕获的全周期中，AI 几乎无处不在：它可能参与了底层漏洞的辅助挖掘，催生了 GitHub 上大量似是而非的假 PoC；我也借助 AI 在半小时内搭建了全流量捕获蜜罐、辅助反汇编与源码分析，甚至你现在读到的这篇复盘长文，大部分骨架与推导也都是我与 AI 协同生成的。

本文将结合我自建蜜罐的第一手日志，深入拆解 php2shell 的底层内核机理，还原在野样本的堆风水细节，并复盘这次充满“AI 特征”的攻防对抗。

---

## 1. 早期验证：那份带偏方向却能触发崩溃的假 PoC

在官方补丁公布前约 24 小时，GitHub 上就冒出了一个声称实现“php2shell 武器化利用”的公开仓库，附带约 39MB 的利用 bundle（解压后有 42MB 冗余符号）。

该仓库构建了一套言之凿凿的利用模型：
> “第二次 `update()` 触发时会释放缓存的 `zval*` 所指向的 session 数组，随后 `FILE_DATA` 的写入直接落入被回收的 320 字节 bin；配合 149 个 `t[]` 堆喷重占位，最终通过 `zend_call_function` 劫持执行流完成 RCE。”

拿到这份材料后，我立刻在本地搭了调试环境（Windows 10 x64 + PHP 8.0.2 / 8.5.4 NTS，配合 WinDbg 和源码符号）进行黑盒与白盒测试：

1. **有限的崩溃复现**：在连续打入畸形 multipart 数据包时，环境确实出现了偶发性的 Worker SIGSEGV 崩溃与内存非法访问。这证明特定形态的表单字段确实能扰乱执行流；
2. **无法推进的 RCE 链**：然而，一旦试图把这个崩溃往“任意代码执行”推进，整条利用链就彻底卡死。我使用带独立序列号与 md5 的 149 个 288 字节分块进行堆喷跟踪，连续 5 轮下来所有 chunk 完整度 100%，没有任何内存覆写发生；
3. **源码核对戳穿了伪机制**：
   - 在 `ext/session/session.c` 中，`Z_TRY_ADDREF(progress->data)` 显式保证了 session 结构体的引用计数不归零；
   - 全文搜索 `zend_call_function`，匹配结果为 **0**。这表明该 PoC 描述的控制流劫持路径完全是拼凑伪造的。

这并不是验证过程中的失误，而是典型的**被劣质利用链带偏**。事后复盘来看，这份在 GitHub 上疯传的 PoC 大概率是利用大语言模型（LLM）根据散落的漏洞描述“脑补”出来的幻觉代码：它拼凑了真实的堆分配术语，甚至碰巧用畸形请求触发了进程段错误，但核心的 RCE 逻辑全属虚构。

直到 10 月 21 日官方补丁（commit `31c0ea7d7f`）公开，真实的根因才浮出水面：真正的利用链根本不需要绕弯子搞引用计数，而是 **OOM 触发 `longjmp` 强制打断原生调用栈后的状态倒挂**。

---

## 2. 内核机制深度剖析：时序错位与状态悬垂

php2shell 包含两个独立的 CVE，它们分别对应着同请求和跨请求两种完全不同的破坏模型。

```
SAPI 接收请求
  └─ php_hash_environment()            [致命点：在此处解析 multipart body]
       └─ rfc1867 回调进入 session 模块
            └─ php_session_initialize() [生命周期倒挂：模块尚未正式 RINIT 即被激活]
  └─ zend_activate_modules()            [扩展模块正常的运行时初始化]
```

### 2.1 架构缺陷：解析请求早于模块 RINIT

在 `main/main.c` 的经典架构中，`php_hash_environment()` 负责解析请求数据（GET/POST/Cookie），而各个扩展的运行时初始化 `zend_activate_modules()` 发生在它**之后**。

当请求体包含 `PHP_SESSION_UPLOAD_PROGRESS` 时，RFC 1867 解析器在脚本执行前便提前回调了 Session 扩展的初始化函数 `php_session_initialize()`。此时模块在尚未完成标准 RINIT 的半生不熟状态下强行分配内存并处理输入。

### 2.2 触发扳机：用 OOM 触发 `zend_bailout()`

当攻击者通过嵌套空文件（`filename=""` 不计入 `max_file_uploads` 限制，却会初始化 HashTable）或超长字段将内存逼近 `memory_limit` 时，一旦 `php_session_initialize()` 内部的 `emalloc` 失败，Zend 引擎就会调用 `zend_bailout()`：

```c
#define zend_bailout() _zend_bailout(__FILE__, __LINE__)
ZEND_API void _zend_bailout(const char *filename, uint32_t lineno) {
    longjmp(*EG(bailout), 1); // 粗暴展开执行栈，跳过一切局部清理
}
```

标准 C 的 `longjmp` 会直接将 CPU 控制权转交到最外层的 Bailout 处理器，所有配对的资源释放逻辑（如 `php_session_flush()`、`PHP_VAR_UNSERIALIZE_DESTROY()`）全部被跳过。

### 2.3 CVE-2026-109618（同请求）：mod_php 的二次释放破坏

主要影响 Apache 的 `mod_php`。`sapi_apache2.c` 的容错逻辑存在缺陷：即便在启动解析阶段发生了 OOM 中断，Apache 依然会调度 `php_apache_request_dtor()`，进而触发 `php_request_shutdown()`。

关闭流程尝试对处于半初始化、未分配完全或字段悬垂的 Session 结构执行析构，直接引发 **Double Free** 与 **Free List 污染**，导致 Apache Worker 内存结构损坏。

### 2.4 CVE-2026-109619（跨请求）：进程复用与悬垂指针

相比同请求，这条链更加通用且隐蔽：

1. **投毒阶段（Request A）**：攻击者让请求 A 在反序列化处理期间发生 OOM、超时或致命错误。由于清理宏被跳过，全局的反序列化器上下文 `BG(unserialize)` 残留在进程持久内存中；
2. **请求重置**：请求 A 结束时，Zend MM 释放了该请求所占用的堆空间，但全局变量里的指针并未置空，变成了**悬垂指针（Dangling Pointer）**；
3. **触发阶段（Request B）**：同一个 Worker 进程在接管请求 B 时，在 `php_hash_environment()` 中再次触发 upload progress 反序列化。解码器检测到 `BG(unserialize)` 非空，误认为是“嵌套递归解析”，直接将新数据追加写入旧上下文；
4. 解析到引用语法（`R:` / `r:`）时，反序列化器直接根据悬垂指针读取已经释放的内存，造成严重的 **Use-After-Free (UAF)**。

> **澄清：PHP-FPM 并不是“天然免疫”**  
> 早期不少分析草率地认为“FPM 退出机制能规避此漏洞”，这是对两个 CVE 的混淆。CVE-2026-109618 的同请求路径确实会因为 FPM 遇到启动失败直接退出 Worker 而失效；但 **CVE-2026-109619 依赖的是跨请求的进程复用**，只要 FPM 开启了长生命周期 Worker 复用（绝大多数生产环境的默认配置），悬垂全局指针的风险就客观存在。**目前没有看到公开的 FPM 稳定武器化利用，只是因为多进程并发碰撞与内存对齐难度极高，绝不等于 FPM 在机制上具备免疫力。**

---

## 3. 蜜罐捕获：Meridian Pay 外壳下的真实攻防数据

在官方漏洞公布后，我使用 AI 协同编写部署了一个无出网能力的低交互混合蜜罐。从 2026-10-21 18:14 到 10-30 07:20 UTC，蜜罐累计运行了 9 天。

### 3.1 诱饵环境与采集架构

蜜罐以 **Meridian Pay（跨境商户结算门户）** 作为业务伪装，运行在 Ubuntu 22.04 容器中，暴露了文档上传、回执下载以及多处历史漏洞诱饵：

| 诱饵层级 | 部署形态 | 攻防意图 |
|---|---|---|
| 核心业务面 | PHP 8.5 运行时（对外 Header 伪装为未打补丁的 8.4.4） | 吸引针对 upload progress 的特定版本探测 |
| 弱点端点 | `/download.php?file=` | 诱捕针对 Session 文件的 LFI 包含动作 |
| 扩展诱饵 | `/blog/` 下挂载 WordPress 6.4.3 及历史插件残留 | 吸引扫描器指纹识别，掩护核心业务捕获面 |
| 静态诱饵 | `.env`、`wp-config.php.bak`、`/status.php` 等 | 记录凭据嗅探与状态探测 |

数据采集采用“PHP 层 + Nginx Mirror 双轨制”：
- **PHP 采集层**：将 `session.upload_progress.cleanup` 强制置为 `Off`，拦截落盘的原始 `sess_<sid>` 快照；
- **Nginx Mirror 镜像层**：利用反向代理在请求进入 PHP 之前全量克隆原始 HTTP 报文，写入独立存储卷，解决 PHP RFC1867 解析器默认“消费掉”原始 multipart 字节导致无法追溯 Raw Body 的问题。

### 3.2 整体流量概况

9 天观测期内，蜜罐共记录了 **23,993 条事件**（已剔除 89 条自测标签及 443 条自测 IP）、来自 **711 个独立 IP**，捕获了 **45,580 份原始请求报文** 与 **17,872 个隔离样本/会话快照**。

```
事件类型分布 (Total: 23,993)
├── wp_login_attempt  : 17,932 (74.7%) ── 集中于单一 IP 暴力字典破发
├── scan              :  3,121 (13.0%) ── 通用扫描、指纹探测
├── view              :  1,920 ( 8.0%) ── 基础页面翻阅
├── recon             :    892 ( 3.7%) ── /status.php, /phpinfo.php 等
└── upload / others   :    128 ( 0.6%) ── 核心上传/投毒行为 (含 20 次重点 spray)
```

整体流量呈现极端的尖峰特征：10 月 27 日单日爆出 18,337 条事件，主要来自 `8.137.104.136` 在 2 小时 51 分钟内发起的 17,932 次 WordPress 登录暴力轮询（使用 `admin` 账号配合 17,616 个完全不同的口令哈希，平均 1.7 次/秒）。这证明 WordPress 诱饵成功吸引了大部分噪点流量。

而在这些海量扫描噪声深处，一组发生在 10 月 25 日的异常请求被系统精准标红。

---

## 4. 样本解剖：81 秒内的 20 次静默堆塑形

2026-10-25 13:26:28 至 13:27:49 UTC，源 IP `45.148.10.183` 向 `/index.php` 发起了 **20 次连续的 POST 请求**。

```
时间轴 (共 81 秒，标记为 20 次绝对重放):
0s     10s    20s    30s    40s    50s    60s    70s    80s
●──●──●──●────●──●───●──●──●──●───●──●──●──●──●───●──●──●─────●
#1    #3     #5     #7    #9    #11    #13   #15   #17  #19   #20
```

### 4.1 载荷特征分析

所有 20 次请求的 Body SHA256 哈希全部一致（`5a88f0cf1dbefe09bc67c3005c34f60493e5e4a31dcd46d8d9622a3e43127034`），单次请求体积固定为 **84,686 字节**，共包含 **203 个 Form-Data Part**，没有任何 User-Agent。

原始报文结构节选：

```http
POST /index.php HTTP/1.1
Host: 106.75.19.171
Content-Type: multipart/form-data; boundary=CCCCCCCCCC
Content-Length: 84686
Connection: close

--CCCCCCCCCC
Content-Disposition: form-data; name="PHPSESSID"

aaaaaaaaaaaaaaaaaaaaaaaaaa
--CCCCCCCCCC
Content-Disposition: form-data; name="PHP_SESSION_UPLOAD_PROGRESS"

kkkkkkkk... [严格填满 4,000 个字符 'k'] ...kkkkkkkk
--CCCCCCCCCC
Content-Disposition: form-data; name="spray0"; filename="s0"

SSSSSSSS... [256 字节字符 'S'] ...SSSSSSSS
--CCCCCCCCCC
Content-Disposition: form-data; name="spray1"; filename="s1"

SSSSSSSS... [256 字节字符 'S'] ...SSSSSSSS
... [连续递增至 spray199，均为 256 字节 'S'] ...
--CCCCCCCCCC
Content-Disposition: form-data; name="uaf"; filename="u.bin"

DDDDDDDD... [4,608 字节字符 'D'] ...DDDDDDDD
--CCCCCCCCCC--
```

蜜罐落盘的对应会话快照文件（`sess_aaaaaaaaaaaaaaaaaaaaaaaaaa`）大小为 4,104 字节，文件开头为序列化后的键：
```
upload_progress_kkkkkkkk...
```
这表明 PHP 已经如攻击者预期，把这 4,000 字节的自定义键和随后的 200 个文件属性写回了 Session 存储。

### 4.2 为什么判定它是一次未完成的底层堆塑形？

这组样本有几个极其反常的特征：

1. **零 Webshell 载荷**：整个 84KB 的请求体中，没有出现任何 `<?php`、`eval`、`base64_decode` 或系统调用函数。全部是机械填充的 `0x53`（'S'）与 `0x44`（'D'）；
2. **零文件包含动作**：在整个 81 秒内及随后的数小时里，该 IP 没有向 `/download.php` 或任何其他页面发起过带有 `sess_aaaaaaaa...` 路径的包含尝试，说明其测试目标根本不是传统的 LFI；
3. **精准的内存对齐布局**：
   - **200 × 256 字节分块（`spray0`~`spray199`）**：在 Zend 内存管理器（Zend MM）中，256 字节属于典型的小块分配尺寸（Size Class Bin）。通过连续喷射 200 个同尺寸 chunk，目的是耗尽当前的 Free List 碎片，使后续分配落在连续平整的全新内存页上；
   - **4,608 字节大块（`name="uaf"`）**：紧随其后申请 4.5KB 的越级大块，用于制造跨页内存空洞，直接为后续的 UAF 引用占位提供可控的内存边界；
4. **直白的调试指纹**：攻击者在分块字段名中毫不掩饰地写死 `name="uaf"`，表明这绝非全自动扫描器的随机载荷，而是一名攻击者正在针对在野目标反复调试其编写中的 Exploit 堆排布参数；
5. **Worker 命中试探**：20 次请求以 2.4s 至 16s 的间隔重放，意在利用并发轮询尝试命中同一个后台 Worker 进程，试探能否引发该 Worker 的静默崩溃。

由于我们的后端运行的是受支持且打全防御补丁的 PHP 8.5 环境，攻击者的这轮堆塑形并未能真正触发 OOM 悬垂，利用链在 81 秒后停滞。但这段留存在蜜罐中的完整原始报文，清晰记录下了漏洞公开仅数天内在野攻击者的实战工程化演进。

---

## 5. 攻防思考：AI 时代的漏洞与安全演进

追踪这次 php2shell 的全流程，让我最感慨的不仅是技术细节本身，而是整个安全研发与对抗节奏的质变：

1. **AI 辅助挖掘正在降低底层漏洞的挖掘门槛**：
   php2shell 的核心成因是几十年来少有人质疑的架构边界问题（RINIT 滞后与 OOM `longjmp`）。这类隐蔽的状态机生命周期缺陷，以往往往依赖经验极其丰富的高级安全研究员数月审计才能定位。随着代码大模型和自动化符号执行工具的结合，类似深层 Native 架构的缺陷挖掘速度被成倍压缩；
2. **AI 污染正在加剧开源情报的“信噪比灾难”**：
   在漏洞披露的前后 48 小时内，GitHub 上涌现出数十个打着“php2shell exploit”标签的仓库。从早期的虚构引用计数利用包，到各种带毒脚本，绝大多数都是用大模型批量生成的代码垃圾。AI 使得制造一份“看起来头头是道”的假 PoC 变得极具欺骗性，极大地干扰了安全团队的技术研判；
3. **防守方同样在被 AI 深度武装**：
   在整个分析过程中，我从接到情报、利用 AI 协助在半小时内写出 Nginx 镜像与 Session 快照采集脚本，到借助 LLM 快速梳理 Zend 引擎在 `var_unserializer` 中的宏展开过程，再到用 AI 快速格式化蜜罐原始数据、生成自动化分析图表——甚至这篇万字深度长文的文字重组，AI 都作为核心工具参与其中。

**攻防对抗已经彻底演变为使用 AI 的人与使用 AI 的人之间的对抗。** 面对越来越向底层 Native 下沉、在应用层“毫无特征”的内存级攻击，守方依靠单纯的关键词 WAF 规则已基本失效；唯有深入到引擎运行时的时序结构、建立异常请求维度的拓扑建模，才能在混乱的噪音中把致命的在野试探剥离出来。

---

### 附：蜜罐捕获在野样本 IOC 汇总

| 属性 | 取值 |
|---|---|
| **攻击源 IP（Spray 探测）** | `45.148.10.183` |
| **关联源 IP（WordPress 爆破）** | `8.137.104.136`（17,932 次 / 17,616 字典哈希） |
| **请求体哈希 (SHA256)** | `5a88f0cf1dbefe09bc67c3005c34f60493e5e4a31dcd46d8d9622a3e43127034` |
| **单请求规整参数** | 84,686 字节 / 203 个 Part |
| **特征 Session 标识** | `PHPSESSID=aaaaaaaaaaaaaaaaaaaaaaaaaa` |
| **注入 Key 前缀** | `PHP_SESSION_UPLOAD_PROGRESS` = 4,000 个字符 `k` |
| **特征分块命名** | `spray0`~`spray199`（每个 256B）、`uaf`（4,608B，文件名 `u.bin`） |
| **事件捕获窗口** | 2026-10-25 13:26:28 ~ 13:27:49 UTC（共 20 次同 Body 重放） |
