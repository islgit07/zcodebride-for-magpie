# magpie-zcode-bridge

magpie 的 OpenCode provider 插件：把本地 **zcode-bridge** 网关（OpenAI chat-completions 兼容接口，前置一个 GLM Coding Plan）挂成 magpie 的 provider `zcode-bridge`，让 magpie 服务的一切 agent（Codex、Claude Code、OpenCode……）都能选 `zcode-bridge/glm-5.3-flash` 这类模型，走桥接背后的计划配额。

An OpenCode provider plugin for magpie: it serves a local **zcode-bridge** gateway (an OpenAI chat-completions compatible endpoint fronting a GLM coding plan) as the magpie provider `zcode-bridge`.

## 安装 / Install

```sh
magpie plugin add github:islgit07/zcodebride-for-magpie
```

或从 npm（如已发布）：

```sh
magpie plugin add npm:magpie-zcode-bridge
```

装好后运行一次登录（桥接不校验密钥，任意值即可）：

```sh
magpie plugin login zcode-bridge
```

## 前置条件 / Prerequisites

本机需运行一个 OpenAI chat-completions 兼容的桥接网关，默认地址：

- `http://127.0.0.1:20131/v1`（zcode-bridge 默认端口）

任何暴露 `/v1/chat/completions` 与 `/v1/models` 的 OpenAI 兼容网关都可用。

## 配置 / Options

默认不需要任何配置。如需自定义端点或密钥：

```sh
magpie plugin options magpie-zcode-bridge '{"baseUrl": "http://127.0.0.1:20131/v1", "apiKey": "sk-..."}'
```

- `baseUrl`：桥接网关地址（默认 `http://127.0.0.1:20131/v1`）
- `apiKey`：发给网关的 Bearer 密钥（默认 `sk-local`，桥接不校验时随意）

## 模型列表 / Models

插件会实时读取网关的 `/v1/models` 作为模型列表；网关不可用时回退到内置的 `glm-5.3-flash`、`glm-5.3`。

## 工作原理 / How it works

插件通过 magpie 的 provider 插件接口注入一个 `@ai-sdk/openai-compatible` provider；请求由 magpie 统一翻译（Codex 的 Responses 协议、Claude 的 Messages 协议等都会被转成 chat completions 发给桥接），因此桥接只需实现最简单的 chat 协议。

## 隐私 / Privacy

本插件不含任何密钥、账号或机器信息；所有配置都在你本机的 magpie 里。

## 致谢 / Credits

由 **ZCode**（编码 agent，运行 **GLM-5.3-Flash** 模型）编写。
Written by **ZCode** (the coding agent), running the **GLM-5.3-Flash** model.

## License

MIT
