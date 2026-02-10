# 📡 Telecom Complaint Handling Chatbot

An AI-powered, multilingual chatbot that exclusively handles **telecom sector** customer complaints. Built with **Flask** and **Azure OpenAI GPT-4o-mini**.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Telecom-Only Gate** | Uses GPT to verify every query is telecom-related; non-telecom queries are politely rejected |
| **Multilingual** | Auto-detects user language and responds in the same language (Hindi, Spanish, French, etc.) |
| **Menu-Driven Flow** | 5 major sectors → sub-processes → query input → resolution |
| **Semantic Routing** | When user picks "Others", GPT identifies the closest matching subprocess |
| **Resolution Engine** | Generates 4-6 actionable self-help steps + escalation paths |
| **Modern Chat UI** | Dark-themed, mobile-friendly conversational interface |

---

## 🏗 Architecture & Flow

```
User Opens Chatbot
        │
        ▼
  ┌─────────────────┐
  │  Welcome Message │ ← Multilingual notice
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │  Select Sector   │ ← Mobile / Broadband / DTH / Landline / Enterprise
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │ Select Subprocess│ ← Billing, Network, SIM, etc. + "Others"
  └────────┬────────┘
           │
     ┌─────┴──────┐
     │  "Others"?  │
     └─────┬──────┘
       Yes │        No
           ▼         ▼
   ┌──────────┐  ┌──────────────┐
   │ User     │  │ User enters  │
   │ describes│  │ complaint    │
   │ issue    │  └──────┬───────┘
   └────┬─────┘         │
        ▼               │
  ┌───────────┐         │
  │ Semantic   │        │
  │ Subprocess │        │
  │ Detection  │        │
  └─────┬─────┘        │
        └───────┬───────┘
                ▼
       ┌────────────────┐
       │ Telecom Check  │ ← GPT validates query is telecom-related
       └────────┬───────┘
          Yes   │    No
                ▼     ▼
    ┌───────────┐   ┌──────────────┐
    │ Language   │   │ Rejection    │
    │ Detection  │   │ Message      │
    └─────┬─────┘   └──────────────┘
          ▼
    ┌───────────────┐
    │ Generate      │
    │ Resolution    │ ← 4-6 steps + escalation info
    │ Steps (in     │
    │ user language)│
    └───────────────┘
```

---

## 📂 Project Structure

```
telecom-chatbot/
├── app.py              # Flask backend + Azure OpenAI integration
├── templates/
│   └── index.html      # Chat UI (HTML/CSS/JS, self-contained)
├── .env.example        # Environment variable template
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 🚀 Setup & Run

### 1. Prerequisites
- Python 3.9+
- Azure OpenAI resource with **GPT-4o-mini** deployed

### 2. Clone & Install
```bash
cd telecom-chatbot
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
```
Edit `.env` with your Azure credentials:
```
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
```

> **Finding your credentials:**
> Azure Portal → your OpenAI resource → **Keys and Endpoint** (left sidebar)
> Deployment name is whatever you named your GPT-4o-mini deployment.

### 4. Run
```bash
python app.py
```
Open **http://localhost:5000** in your browser.

---

## 📋 Telecom Menu Structure

| # | Sector | Subprocesses |
|---|--------|-------------|
| 1 | 📱 Mobile Services | Billing, Network, SIM/Activation, Data Plans, Roaming, MNP, Call/SMS, Others |
| 2 | 🌐 Broadband/Internet | Speed, Disconnections, Billing, Installation, Router, DNS/IP, Others |
| 3 | 📺 DTH/Cable TV | Channels, Set-Top Box, Billing, Signal Quality, Plans, Others |
| 4 | ☎️ Landline | Dial Tone, Call Quality, Billing, Connection, Fault Repair, Others |
| 5 | 🏢 Enterprise | SLA, Leased Line, Corporate Plans, Cloud/VPN, Tech Support, Others |

---

## 🌐 Multilingual Support

The chatbot auto-detects user language from their query input. Examples:

- **Hindi**: "मेरा इंटरनेट काम नहीं कर रहा है" → Response in Hindi
- **Spanish**: "Mi conexión a internet es muy lenta" → Response in Spanish
- **French**: "Mon téléphone n'a pas de réseau" → Response in French

---

## 🔧 Customization

### Add/Modify Sectors
Edit the `TELECOM_MENU` dictionary in `app.py`:

```python
TELECOM_MENU = {
    "6": {
        "name": "5G Services",
        "icon": "⚡",
        "subprocesses": {
            "1": "5G Coverage Issues",
            "2": "Device Compatibility",
            "3": "Others",
        },
    },
    # ...
}
```

### Adjust Resolution Style
Modify the system prompt in `generate_resolution()` to change tone, step count, or format.

---

## 📄 License

MIT — use freely for your projects.
