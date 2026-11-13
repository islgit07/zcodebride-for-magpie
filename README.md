# zcodebride-for-magpie
> 本插件由Zcode使用glm-5.3-flash免费鸡蛋编写

## 这是做什么的

 magpie 的Zcode通道会被限流，本插件把azrinaldi的zcode-bridge引入到magpie，方便路由。

我只试过Codex 其他 agent还请自行配置优化 

## 前置安装

- **[zcodebride-for-magpie](https://github.com/yetone/magpie)）**：API转接路由
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


MIT