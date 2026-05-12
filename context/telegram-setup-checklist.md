# Telegram Bot Setup — Quick Checklist

Do these in order. Should take ~30 min.

---

## Step 1 — Get Anthropic API Key
- [ ] Go to console.anthropic.com
- [ ] API Keys → Create Key → name it `jarvis-n8n`
- [ ] Copy the key (starts with `sk-ant-...`) — save it, you won't see it again
- [ ] Add $5 credit in Billing (lasts months)

---

## Step 2 — Create Telegram Bot
- [ ] Open Telegram → search @BotFather
- [ ] Type `/newbot`
- [ ] Name: `Jarvis`
- [ ] Username: something like `myjarvis_bot` (must end in `_bot`)
- [ ] Copy the Bot Token BotFather gives you — save it

---

## Step 3 — Set Up n8n
- [ ] Go to n8n.io → Get started free → create account

---

## Step 4 — Build the Workflow in n8n
- [ ] New Workflow → name it `Jarvis Telegram Bot`
- [ ] Add node: **Telegram Trigger** → credential = your Bot Token → Updates = Message
- [ ] Add node: **AI Agent** → Model = Anthropic → API Key = your Anthropic key → Model = `claude-sonnet-4-6`
- [ ] In AI Agent System Message → paste contents of `scripts/agent-system-prompt.md`
- [ ] In AI Agent User Message → set to `{{ $json.message.text }}`
- [ ] Add node: **Telegram → Send Message** → Chat ID = `{{ $('Telegram Trigger').item.json.message.chat.id }}` → Text = `{{ $json.output }}`
- [ ] Hit **Activate** (top right toggle)

---

## Step 5 — Test It
- [ ] Open Telegram → find your bot → send it a message
- [ ] Should respond within a few seconds
- [ ] If not: check n8n Executions tab for errors

---

## Once Live — What It Can Do
- Answer questions, give advice, help with decisions
- Trading accountability from your phone
- Help with business decisions (insurance, capital planning)

## What It Cannot Do
- Access your workspace files or run slash commands
- Access external accounts (Tradovate, etc.)

---

**Full setup guide:** `reference/telegram-n8n-setup-guide.md`
