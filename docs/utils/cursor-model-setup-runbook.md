# Adding the RTU proxy models to Cursor

Prerequisite: the proxy is already live at `https://llm.rdi.services/v1` and tested working with
curl (see the main runbook). This is just the Cursor-side wiring.

---

## 1. Open Model settings

**Cursor → Settings → Cursor Settings → Models**

---

## 2. Set the API key

Scroll to **API Keys → OpenAI API Key**:

1. Paste in your `PROXY_MASTER_KEY` (the same value from `~/rtu-proxy/.env` on the droplet).
2. Turn the toggle **on** (green). If it stays gray/off, the key won't actually be sent with
   requests even though it shows "Secret saved".

---

## 3. Set the base URL override

Still on the same page, **Override OpenAI Base URL**:

1. Toggle it **on**.
2. Enter:
   ```
   https://llm.rdi.services/v1
   ```

---

## 4. Add the custom models

Further up on the Models page, find the **"Enter model name"** field and add each model from
`config.yaml` one at a time, clicking **Add** after each:

```
rtu-opus-5
rtu-sonnet-5
rtu-fable-5
```

After adding, make sure each one's toggle is switched **on** (green). Newly added models
sometimes default to off.

---

## 5. Avoid conflicts

If Cursor has a separate **Anthropic API Key** enabled anywhere in these settings, turn it
**off**. Having both an Anthropic BYOK key and an OpenAI base-URL override active at the same
time is known to cause Cursor to misroute Claude traffic.

---

## 6. Restart Cursor

Fully quit and reopen Cursor so the new custom models are picked up in the model list.

---

## 7. Test it

1. Open a chat.
2. Click the model picker, select `rtu-sonnet-5` (or `rtu-opus-5` / `rtu-fable-5`).
3. Send a simple message like "hi".

If you get a normal reply, it's working end to end.

---

## If it doesn't respond

On the droplet, watch the proxy logs live while you send a message from Cursor:

```bash
sudo journalctl -u rtu-proxy -f
```

- **Nothing appears when you send from Cursor** → the request isn't reaching the droplet at all.
  Re-check the base URL (must end in `/v1`) and that the API key toggle is on.
- **A request appears but errors** → the log will show the actual error (auth, model name
  mismatch, etc.) — compare the model name in the error against your `config.yaml` exactly.
