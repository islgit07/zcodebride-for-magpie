# zcodebride-for-magpie
> 本插件由Zcode使用glm-5.3-flash免费鸡蛋编写

## 这是做什么的

 magpie 的Zcode通道会被限流，本插件把azrinaldi的zcode-bridge引入到magpie，方便路由。

我只试过Codex 其他 agent还请自行配置优化 

## 感谢与前置安装
感谢大佬们开发的应用，免费鸡蛋很好吃。

- **[magpie](https://github.com/yetone/magpie)**：API转接路由
- **[zcode-bridge](https://github.com/azrinaldi/zcode-bridge)**：真正干活的桥，在你电脑上把 GLM 套餐变成一个本地接口。

另外本机安装了ZCode，不太确定是否能不安装ZCode就直接使用，毕竟免费鸡蛋是需要安装才能领到的

## 三步装好
或者把网址发Agent，让Agent帮你安装

1. 安装插件：

```
magpie plugin add github:islgit07/zcodebride-for-magpie
```

2. 登录。

```
magpie plugin login zcode-bridge
```

3. 重启 magpie（或刷新模型列表）。看到 `zcode-bridge/glm-5.3-flash` 这样的模型，就说明成功了。

## 常见问题

**模型列表是空的？**
多半是本地网关没在跑。确认 ZCode 处于打开状态，再刷新一次。

**想改网关地址？**
本地端口在20131

```
magpie plugin options magpie-zcode-bridge '{"baseUrl": "http://127.0.0.1:20131/v1"}'
```

## keeper（让桥接自动开、自动关）

插件本身不会帮你启动 zcode-bridge。仓库里带了个小脚本 `keeper.py`（Windows 专用）：

- 哪个 agent 切到 `zcode-bridge/*` 模型，就自动拉起桥接；全切走且 10 分钟没请求，就自动关掉
- 桥接的 JWT 过期导致 401 时，自动重启换新票

用法（Python 3）：

```
python keeper.py
```

路径想改的话用环境变量：`ZCODE_BRIDGE_EXE`、`MAGPIE_CONFIG_DIR`、`CODEX_CONFIG`。

开机自启：在启动文件夹（`Win+R` 输入 `shell:startup`）放一个 `.vbs`：

```vbs
CreateObject("WScript.Shell").Run """pythonw.exe的路径"" ""keeper.py的路径""", 0, False
```


MIT
