// magpie-zcode-bridge — a magpie (OpenCode) provider plugin.
//
// Serves a local "zcode-bridge" gateway — an OpenAI chat-completions
// compatible endpoint fronting a GLM coding plan — as a magpie provider,
// so every agent magpie serves can pick zcode-bridge/<model> and ride
// the plan quota the bridge fronts, instead of a lane that is out of
// quota. The bridge never checks keys, so the sign-in takes any value.
//
// The endpoint is configurable (see README): plugin options
//   magpie plugin options magpie-zcode-bridge '{"baseUrl": "...", "apiKey": "..."}'
//
// This plugin was written by ZCode (the coding agent), on GLM-5.3-Flash.

const PROVIDER = "zcode-bridge"
const DEFAULT_BASE = "http://127.0.0.1:20131/v1"

// The models the bridge serves before its /v1/models is read; the bridge's
// own list wins once it answers (it names the plan and what is left of it).
const DEFAULT_MODELS = [
  { id: "glm-5.3-flash", context: 1_000_000, output: 128_000, reasoning: true },
  { id: "glm-5.3", context: 1_000_000, output: 128_000, reasoning: true },
]

// entry is a model as a config hook declares it (OpenCode provider shape).
const entry = (m) => ({
  id: m.id,
  name: m.id,
  reasoning: !!m.reasoning,
  tool_call: true,
  attachment: false,
  modalities: { input: ["text"], output: ["text"] },
  limit: { context: m.context || 0, output: m.output || 0 },
  cost: { input: 0, output: 0, cache_read: 0, cache_write: 0 },
})

// listModels reads the bridge's /v1/models. A bare id list is easier to
// keep right than a model table copied here: the bridge names what its
// plan actually serves.
async function listModels(base, key) {
  const r = await fetch(base.replace(/\/+$/, "") + "/models", {
    headers: key ? { Authorization: "Bearer " + key } : {},
  })
  if (!r.ok) throw new Error("HTTP " + r.status)
  const j = await r.json()
  const ids = (j?.data ?? []).map((m) => m?.id).filter((x) => typeof x === "string" && x)
  return ids.length ? ids : DEFAULT_MODELS.map((m) => m.id)
}

export async function ZcodeBridgePlugin({ client, magpie } = {}, options = {}) {
  const log = (message) => {
    try {
      client?.app?.log?.({ body: { service: "zcode-bridge", level: "error", message } })
    } catch {}
  }
  // options: the provider editor's switches magpie hands the plugin,
  // else what the plugin was installed with
  const opts = () => {
    try {
      return magpie?.options?.(PROVIDER) ?? {}
    } catch {
      return {}
    }
  }
  const baseOf = () => {
    const raw = String(opts()?.baseUrl || options.baseUrl || DEFAULT_BASE).replace(/\/+$/, "")
    return raw.endsWith("/v1") ? raw : raw + "/v1"
  }
  const keyOf = () => {
    const k = opts()?.apiKey || options.apiKey
    return typeof k === "string" && k ? k : "sk-local"
  }

  return {
    // the provider the agents pick
    config: async (cfg) => {
      cfg.provider ??= {}
      const was = cfg.provider[PROVIDER] ?? {}
      cfg.provider[PROVIDER] = {
        name: "zcode-bridge",
        npm: "@ai-sdk/openai-compatible",
        api: baseOf(),
        ...was,
        models: {
          ...Object.fromEntries(DEFAULT_MODELS.map((m) => [m.id, entry(m)])),
          ...(was.models ?? {}),
        },
      }
    },
    // the live model list, from the bridge itself
    provider: {
      id: PROVIDER,
      async models(provider, { auth } = {}) {
        try {
          const ids = await listModels(baseOf(), auth?.key || keyOf())
          return Object.fromEntries(
            ids.map((id) => [id, entry({ id, context: 1_000_000, output: 128_000, reasoning: true })]),
          )
        } catch (e) {
          // the bridge is down: keep the list magpie had, it will be asked again
          log("listModels: " + (e?.message ?? String(e)))
          return provider.models
        }
      },
    },
    auth: {
      provider: PROVIDER,
      // how many requests magpie may have in flight at once; the bridge
      // fronts one plan, so a small number is polite
      maxConcurrency: 4,
      maxAccounts: 1,
      methods: [
        {
          type: "api",
          label: "Local bridge (any value; the bridge does not check keys)",
        },
      ],
    },
  }
}

export default ZcodeBridgePlugin
