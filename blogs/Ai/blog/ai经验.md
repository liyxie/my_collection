转载自：[刚注册两天，但已经在L站与I站逛了一两个月了，把自己全部的所学与经验分享给大家 - 搞七捻三 / 搞七捻三, Lv1 - LINUX DO](https://linux.do/t/topic/1809325)

### 1. 模型的选择

**网页对话**：目前我网页对话用的是 [Google AI Studio](https://aistudio.google.com/prompts/new_chat) 里的 **Gemini 3 Flash High**，3 flash不如最顶尖的模型，但开high处理日常问题和任务是基本够用的，主要是对话额度也够。之前的 3 Pro 额度非常多，可以基本无限对话，现在 3.1 Pro 额度极少并且思考很慢，用 3 Flash 可以完美平衡这一点。复杂点的任务可以用3.1 pro，就是现在额度太少对话不了几句，所以一般我都是认为一个任务flash处理不了我才切换到3.1pro。

**搜索方面**：搜索方面 [**Grok**](https://grok.com/) 是全方位的领先。AI Studio 的 Gemini 基本不会自己去搜索，而 Grok 的搜索质量非常高，而且一般都能找到解决方案。[**豆包**](https://www.doubao.com/chat/)也不错，它的**专家模型**的综合能力非常强，网页对话和搜索也可以选择豆包专家模型，不过高峰期用多了会被限制。

**图像生成**：平常可以使用豆包，比较方便并且能力也不错。**Nano Banana** 能力很强，适用于大部分任务，大家可以使用pixel的12个月pro试用来获取google pro会员，下文有写。

**视频生成**：同样可以使用豆包的seedance，但是限制较多。我个人经常使用 [grok imagine](https://grok.com/imagine)，免费用户有一定的额度免费用户已经不再有额度，另外你可以绑卡优惠获取3天的**supergrok试用**获取更高质量的视频和额度，生成的视频效果不错，并且最重要的是*基本*无限制。

**编程代码**：目前也就两个选择，**Claude** 与 **GPT**。
如果你一点都不想折腾，那么 **GPT Team** 就是当下的最优选，找闲鱼上有质保的几块钱一个月，量大好用。站内公益站的 Codex 也基本是管饱的，Codex App 的体验也是一流，真正意义上的 **“vibe coding”**。
Claude 方面可以用站内佬友们的各种公益站，但 Claude 现在其实都不太稳。如果有财力和环境与折腾能力的话可以自己去购买官方订阅，但是容易封号，所以稳定获取其实挺麻烦的。
体感上来看二者能力其实没有一个特别大的明显差别，但是风格有所不同。Claude 好像更灵性，用起来感觉上要舒服点；GPT 的遵循指令能力和逻辑推理能力非常强，配上 Codex App 用起来体验也非常不错。
总之，除非你非要追求极致的体验，编程这方面选 Codex 是完全足够的。

**必装skills和mcp推荐：**

- [ChromeDevTools/chrome-devtools-mcp: Chrome DevTools for coding agents](https://github.com/ChromeDevTools/chrome-devtools-mcp)
  *google官方mcp，让agent能够自行真实调用chorme进行搜索、调试、网页抓取等等。*
- [obra/superpowers：An agentic skills framework & software development methodology that works.](https://github.com/obra/superpowers)
  *一套非常有效的skills，让agent框架与软件开发有一套科学的开发方法论，实测代码生成质量提高不少*

**skill最好的教学视频：**[Agent Skill 从使用到原理，一次讲清](https://www.bilibili.com/video/BV1cGigBQE6n)
***每个skill与mcp你都可以把github仓库链接丢给模型让它自行安装。***

------

### 2. 上网环境与节点推荐

上网环境这方面，隔壁站 [idcflare.com](http://idcflare.com/) 是绝对的专业。由于I站注册没有门槛与邀请，我在I站逛得特别多。

大家可以在I站拼车版块 **[最新拼车话题 - IDC Flare](https://idcflare.com/tag/4-tag/4)**，以极其优惠的价格跟别人拼到各种节点服务器，**甚至是极度纯净的家宽**。我目前的 AI 访问节点就是隔壁拼到的美国家宽，可以顺利注册各种 AI 服务与薅到各种绑卡优惠。

下面是我在隔壁找到的一些极其有用的话题帖（有些佬友可能在双站都有发帖，我只贴我隔壁站看到的）：

- [机圈黑话/专有名词扫盲（持续更新ing） - 教程 - IDC Flare](https://idcflare.com/t/topic/16977)
- [常见家庭宽带vps推荐 - 测评 - IDC Flare](https://idcflare.com/t/topic/41899)
- [VPS IP质量检测完全指南：从小白到精通的实用教程 - 教程 - IDC Flare](https://idcflare.com/t/topic/18792)
- [[教程3.0\] 草履虫也能学会的 Clash 配置：UI界面一键配置精确分流、链式代理 - 教程 - IDC Flare](https://idcflare.com/t/topic/51015)
- [[猫猫教程\]小白优雅的使用NAT机器 - 从入门到实战的完整指南 - 教程 - IDC Flare](https://idcflare.com/t/topic/21816)
  ***你对服务器和节点想了解的一切，在 idcflare 基本都可以找到答案。***

![:graduation_cap:](https://cdn.ldstatic.com/images/emoji/twemoji/graduation_cap.png?v=15)**大学生专属福利与校园网免流技巧**：
另外分享一下大学生的优惠！大学生认证成功 [GitHub Student Pack](https://education.github.com/pack) （github student还有非常多的其他权益，自己可以在认证页面查看）后，在 [DigitalOcean](https://www.digitalocean.com/) 注册可以获得**一年 $200 的免费额度**。这 $200 够我们开两台一年的低配服务器（比如一台新加坡 + 一台洛杉矶）。
**最重要的是 DO 的服务器带有 IPv6 地址！如果你学校有 IPv6 并且 IPv6 免流的话（比如我们学校只收 IPv4 下行流量，IPv6 所有流量免流），你可以把你得到的服务器作为代理上网节点，通过 IPv6 地址代理直接实现**校园网自由！
这里推荐使用 Hysteria2 协议，暴力发包非常适合学校到代理服务器这种网络，我自己实测下来新加坡服务器基本可以吃满带宽。搭建教程如下：

- [SkYFly2233/NEU-ipv6-proxy: 一个基于ipv6代理的校园网免流量方法](https://github.com/SkYFly2233/NEU-ipv6-proxy)

如果你想自建节点，站内和隔壁站都有很多教程我就不赘述了。我目前用的是一键脚本，非常方便不折腾：

- [233boy/sing-box: 最好用的 sing-box 一键安装脚本 & 管理脚本](https://github.com/233boy/sing-box)

我建议每个人都有一个**美国家宽**，有了纯净的ip节点（ip质量检测见上文链接），模型真的会更聪明，最重要的是访问AI服务非常顺畅。

并且这以后你不用再自己买team车位，可以在咸鱼上买**虚拟信用卡**2块左右一张，然后创建一个新号绑定首月business的免费试用，这样花2块就能得到四个team子号（母号少用防止被封）随便你用。买虚拟卡请不要买人多的，容易被封，可以买那种刚上线的还没几个人买的，这种卡一般都还比较干净能绑，邮箱可以用outlook。我自己2块开的已经坚挺了一个星期。

另外，google的学生活动好像不行了，但是现在新出了一个**pixel一年pro试用活动**。我已经成功薅到了优惠。为了防止有引流的嫌疑，大家可以去B站或yt上搜索一下教程，成本下来也才十几块。并且这期间有美国家宽的话绑卡也会更顺利，推荐大家去了解尝试一下。

------

### 3. API 中转站搭建与号池管理

自建的中转站基本都是通过大量的号池反代成 API，并进行统一分发管理。我来到L站后也根据站内教程自建了属于自己的中转站。

我采用的是 **CLIProxyAPI（CPA）反代号池得到上游 API，并使用 New-API 进行分发管理**，这也是目前最主流的方案。你可以用此建立公益站分享给佬友们，或者只给自己与朋友同学使用。教程如下：

- [基于docker搭建CLIProxyAPI图文教程 - 文档共建 - LINUX DO](https://linux.do/t/topic/1672081)
- [基于docker搭建newapi图文教程 - 文档共建 - LINUX DO](https://linux.do/t/topic/1672089)

搭建好后，如果你有自己的域名，可以把域名托管到 Cloudflare：

- [【教程】2026版 小白也能看懂的自建Cloudflare临时邮箱教程（域名邮箱） - 文档共建 - LINUX DO](https://linux.do/t/topic/1666961)
  *(如果只是想托管域名，看教程第一部分即可，当然也很推荐顺手搭一个自己的域名邮箱。)*

**域名解析与反代小贴士**：
在 DNS 记录里，把你的域名解析到服务器 IP。这样你开的中转站别人就可以通过你的域名访问了。前缀可以填 `api`、`cpa` 等。然后在服务器里运行 Nginx 反向代理，把不同子域名的请求转发到不同服务端口。比如让 `api.你的域名.com` 访问 New-API 服务，`cpa.你的域名.com` 访问 CPA 服务。这一块有任何不懂的地方，直接让 Gemini 给你写 Nginx 配置即可，非常简单。

**号源获取**：
目前的 Codex 普号还是很容易弄的，站内有很多佬友天天分享自己新注册的几百个 Codex 号，你可以下载导入到 CPA 里面反代。但这种号死得比较快，进阶玩法是用注册机进行注册（这块需要自己去了解，注意适度）。从此实现 API 自由。

**公益站集中管理**：
对于站内茫茫多的公益站，强烈推荐用 **All-API-Hub** 进行统一的自动签到和管理分发。我目前配合它的浏览器扩展使用，极其方便：

- [All-API-Hub：开源AI中转站集中管理和自己的New API增强管理 - 开发调优 - LINUX DO](https://linux.do/t/topic/1663357)