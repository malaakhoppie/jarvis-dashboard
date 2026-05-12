# Telegram Bot + n8n Setup Guide

Set up a Telegram bot that connects to Claude API via n8n. When complete, you can message your Jarvis bot from anywhere on your phone.

**Time required:** ~30 minutes
**Cost:** Free (n8n free tier) + Anthropic API usage (~$0.01–0.05 per conversation)

---

## What You'll End Up With

```
You (Telegram) → Your Bot → n8n → Claude API → n8n → Your Bot → You
```

A private Telegram bot that only you use. Message it like texting — it responds as Jarvis.

---

## Part 1: Get Your Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in with your Anthropic account
3. Click **API Keys** in the left sidebar
4. Click **Create Key** → name it `jarvis-n8n`
5. Copy the key — it starts with `sk-ant-...`
6. **Save it somewhere safe** (you won't see it again)

> Add a few dollars of credit in **Billing** — $5 will last months at normal usage.

---

## Part 2: Create Your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Start a chat and type: `/newbot`
3. BotFather asks for a name → type: `Jarvis` (or whatever you want to call it)
4. BotFather asks for a username → type something like: `myjarvis_bot` (must end in `_bot`)
5. BotFather gives you a **Bot Token** — looks like: `7123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
6. **Copy and save this token**

---

## Part 3: Set Up n8n Cloud

1. Go to [n8n.io](https://n8n.io) and click **Get started for free**
2. Create an account
3. You'll land in your n8n dashboard

---

## Part 4: Build the Workflow

### Create a new workflow

1. Click **+ New Workflow**
2. Name it: `Jarvis Telegram Bot`

### Add Node 1: Telegram Trigger

1. Click the **+** button to add a node
2. Search for **Telegram Trigger**
3. Select it
4. Under **Credential**, click **Create new credential**:
   - Name: `Telegram Bot`
   - **Bot Token**: paste your Bot Token from Part 2
   - Click **Save**
5. Under **Updates**, select **Message**
6. Click **Save** on the node

### Add Node 2: AI Agent (Claude)

1. Click **+** after the Telegram Trigger
2. Search for **AI Agent**
3. Select **AI Agent**
4. Under **Model**, select **Anthropic**
5. Click **Create new credential** for Anthropic:
   - Name: `Anthropic Jarvis`
   - **API Key**: paste your Anthropic API key from Part 1
   - Click **Save**
6. Under **Model**, choose: `claude-sonnet-4-6`
7. Under **System Message**, paste the entire system prompt from:
   `scripts/agent-system-prompt.md` in your workspace (customize it first)
8. Under **User Message**, click the expression icon `{}` and set it to:
   `{{ $json.message.text }}`
9. Click **Save**

### Add Node 3: Telegram — Send Message

1. Click **+** after the AI Agent
2. Search for **Telegram**
3. Select **Send Message**
4. Under **Credential**, select the Telegram Bot you created earlier
5. Under **Chat ID**, click `{}` and set:
   `{{ $('Telegram Trigger').item.json.message.chat.id }}`
6. Under **Text**, click `{}` and set:
   `{{ $json.output }}`
7. Click **Save**

---

## Part 5: Activate and Test

1. Click the **Activate** toggle in the top right of n8n
2. Open Telegram and find your bot
3. Send it a message: `Hey, what's up?`
4. It should respond within a few seconds

If it doesn't respond:
- Check the n8n **Executions** tab
- Make sure the workflow is activated
- Verify your Anthropic API key has credit

---

## Limitations

| Telegram Bot Can | Telegram Bot CANNOT |
|---|---|
| Answer questions and give advice | Access workspace files |
| Draft emails, captions, messages | Run Claude Code slash commands |
| Help with decisions and strategy | Access Gmail, Notion, or other tools |
| Brainstorm and analyze | Make changes to external systems |

For anything requiring full workspace access, open Claude Code on your Mac.

---

## Optional Enhancements

- **Conversation memory**: Add a "Window Buffer Memory" node so the bot remembers context across a conversation
- **Voice messages**: Add a Telegram → Whisper transcription node before the AI Agent
- **Daily brief**: Add a Schedule Trigger that messages you every morning with a status update
