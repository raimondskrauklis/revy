# Qwen3.8 Local Deployment Runbook

Deploying Qwen3.8 models locally and wiring them into Cursor via LiteLLM + Tailscale Funnel.

## Hardware Profiles

| Target | Hardware | Model | Precision |
|---|---|---|---|
| Laptop | MacBook Pro, Apple M4 Pro, 24GB unified memory | Qwen3.8-27B | 4-bit quant |
| Rig | 2x NVIDIA B300 (576GB HBM3e total) | Qwen3.8-27B | Full BF16 or Qwen3.8-2.4T-A95B (FP4, experimental) |

**Notes:**
- 24GB Mac is at the documented minimum for Qwen3.8-27B. Use 4-bit (UD-Q4_K_XL / MLX-4bit, ~17-19GB). Do not attempt 8-bit (~28GB+) or full BF16 (~56GB) — both exceed available memory.
- Qwen3.8-2.4T-A95B (2.4T total params, 95B active, MoE) officially requires a minimum of 4 B300/GB300 nodes for supported production serving (NVIDIA NIM), or at least 2 full B300/MI355X nodes for community/vLLM inference at FP4. A 2x B300 setup is at the bare floor — only viable with aggressive FP4 quantization and short context. Prefer running Qwen3.8-27B at full precision on this rig instead, where it fits comfortably with large headroom.
- Qwen3.8-27B: 262K native context, extendable to 1M via YaRN. Long context inflates KV-cache memory — budget extra headroom beyond base weight size, especially on the 24GB Mac.

---

## Part 1: Deploy Qwen3.8-27B on MacBook Pro (M4 Pro, 24GB)

### Option A — MLX (recommended, fastest on Apple Silicon)

```bash
# Install MLX inference stack
uv tool install mlx-lm
pip install -U mlx-vlm

# Start OpenAI-compatible local server (auto-downloads weights on first run)
mlx_lm.server --model mlx-community/Qwen3.8-27B-4bit --port 8080

# Or direct CLI generation (vision-capable)
python -m mlx_vlm.generate \
  --model mlx-community/Qwen3.8-27B-4bit \
  --max-tokens 512 \
  --temperature 0.7 \
  --prompt "your prompt here"
```

Optional: `pip install mlx-dspark` for up to ~3x speed improvement on Apple Silicon over standard llama.cpp for this model.

### Option B — LM Studio (GUI, beginner-friendly)

1. Install LM Studio.
2. Discover tab → search "Qwen3.8 27B".
3. Pick the **MLX 4-bit** variant if listed, otherwise **UD-Q4_K_XL GGUF**.
4. Download, load in Chat tab.
5. Set context length conservatively (8K–32K to start) — do not max out 262K on 24GB.
6. Optional: enable local server (`localhost:1234`, OpenAI-compatible) for API access.

### Option C — Ollama (CLI, if tag is published)

```bash
ollama pull qwen3.8:27b
ollama run qwen3.8:27b
```

Check `ollama.com/library` if the tag isn't found yet — availability may lag a few days post-release.

### Memory Safety Checklist (24GB Mac)

- [ ] Use 4-bit quant only (17–19GB). Drop to UD-Q3_K_XL (~13–14GB) if memory pressure appears.
- [ ] Close memory-heavy apps (browsers, IDEs with many extensions) before loading.
- [ ] Start with 8K–32K context; increase cautiously.
- [ ] Avoid Q8/full precision entirely on this machine.

---

## Part 2: Deploy on B300 Rig (2x B300)

Qwen3.8-27B fits with large headroom — run at full BF16 precision via vLLM.

```bash
pip install vllm

vllm serve Qwen/Qwen3.8-27B \
  --tensor-parallel-size 2 \
  --dtype bfloat16 \
  --max-model-len 262144 \
  --port 8000
```

For Qwen3.8-2.4T-A95B (experimental on 2x B300 only — below documented minimum):

```bash
# Requires FP4-quantized weights; short context; no production guarantee at this scale
vllm serve Qwen/Qwen3.8-2.4T-A95B-FP4 \
  --tensor-parallel-size 2 \
  --quantization fp4 \
  --max-model-len 32768 \
  --port 8000
```

Official minimums: 4 nodes (NVIDIA NIM, production) / 2 nodes (vLLM community, FP4). Treat any 2-GPU deployment of the 2.4T model as a proof-of-concept, not a reliable daily driver.

---

## Part 3: LiteLLM Proxy (Unified Gateway)

Routes Cursor requests to local models (Ollama/MLX/vLLM) and cloud models (OpenAI, Anthropic, xAI) through one endpoint.

### Install

```bash
pip install 'litellm[proxy]'
```

### config.yaml

```yaml
model_list:
  - model_name: qwen3.8-27b-mac
    litellm_params:
      model: openai/mlx-community/Qwen3.8-27B-4bit
      api_base: http://localhost:8080/v1
      api_key: sk-fake-key

  - model_name: qwen3.8-27b-rig
    litellm_params:
      model: openai/Qwen/Qwen3.8-27B
      api_base: http://localhost:8000/v1
      api_key: sk-fake-key

  - model_name: qwen3.8-27b-ollama
    litellm_params:
      model: ollama/qwen3.8:27b
      api_base: http://localhost:11434

general_settings:
  master_key: sk-my-secret-key   # replace with a strong key
```

### Launch

```bash
# Mac — use a Funnel-allowed port (443, 8443, or 10000)
litellm --config config.yaml --port 8443 --host 0.0.0.0
```

---

## Part 4: Expose via Tailscale Funnel

Assumes Tailscale is already installed and connected.

### One-time tailnet setup

1. Tailscale admin console → DNS → enable **MagicDNS**.
2. Same page → enable **HTTPS certificates**.
3. Ensure the `funnel` node attribute is granted for your account (first `tailscale funnel` run will prompt via web consent if missing).

### Enable Funnel

```bash
# Foreground (test first)
tailscale funnel 8443

# Background (persists across terminal close / reboot)
tailscale funnel --bg 8443
```

Output gives a stable public URL: `https://<device-name>.<tailnet-name>.ts.net/`

### Running Mac + B300 rig simultaneously

Funnel only supports ports 443, 8443, 10000. Run each machine's LiteLLM instance on a different allowed port:

```bash
# On MacBook Pro
tailscale funnel --bg 8443

# On B300 rig (separate device on same tailnet)
tailscale funnel --bg 10000
```

This gives two independent stable URLs — one per machine.

### Security notes

- Funnel traffic is genuinely public once enabled. Enabling HTTPS also publishes the device's certificate to a public CT log — avoid device names that reveal sensitive info.
- Keep the LiteLLM `master_key` strong; it is the only gate once the URL is public.

---

## Part 5: Configure Cursor

1. Cursor → Settings → Cursor Settings → Models.
2. Enable **Override OpenAI Base URL**.
3. Enter: `https://<device-name>.<tailnet-name>.ts.net/v1`
4. API Key field: your LiteLLM `master_key`.
5. Click **+ Add Custom Model**, enter the exact `model_name` from `config.yaml` (e.g. `qwen3.8-27b-mac` or `qwen3.8-27b-rig`).
6. Enable the toggle for the new model — it now appears in Cursor's model picker alongside Grok, Composer, GPT-5.6, etc.

### Known issue to watch for

Cursor Agent mode can send Anthropic-style tool-call payloads to OpenAI-compatible endpoints, which may crash LiteLLM during agentic/tool-use sessions. Test plain chat completions first before relying on this for full agent workflows. If it breaks, check LiteLLM logs for malformed `tool_result` payloads.

---

## Quick Reference: Full Startup Sequence

```bash
# 1. Start local model server (Mac example, MLX)
mlx_lm.server --model mlx-community/Qwen3.8-27B-4bit --port 8080 &

# 2. Start LiteLLM proxy pointing at it
litellm --config config.yaml --port 8443 --host 0.0.0.0 &

# 3. Expose via Funnel
tailscale funnel --bg 8443

# 4. Point Cursor at https://<device-name>.<tailnet-name>.ts.net/v1
```
