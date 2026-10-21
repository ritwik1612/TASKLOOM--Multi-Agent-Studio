# Taskloom · Multi-Agent Studio

> One request. Many specialist roles. One reviewable result.

Taskloom is a desktop-first, interpretable multi-agent language-processing studio. It turns a natural-language request into a structured workflow: it identifies the request and constraints, plans logical subtasks, produces a response, and shows the resulting trace for review.

## Get started on Windows

Download the v2 Windows installer (**`Taskloom.Setup.exe`** on GitHub Releases) and double-click it.

1. Approve the Windows administrator prompt. This allows the default installation folder to be **`C:\Program Files\Taskloom`**.
2. Keep that location or select **Browse** to install somewhere else.
3. After installation, open **Taskloom** from the installer or by opening `Taskloom.exe` in the selected folder.
4. Select **Connect Gemini** in Taskloom.
5. Choose **Open Google AI Studio**, create a Gemini API key, and paste it as your **primary** key.
6. Optionally add a **backup** key. For independent quota it must belong to a different eligible Google project; two keys from the same project share its limits.

The installer is a single visible file; the app's runtime is placed neatly inside the selected installation folder. Keep `Taskloom Runtime` beside `Taskloom.exe` after installation.

## Your API keys and privacy

- Keys are stored in **Windows Credential Manager**, not in this repository, a download, or a project `.env` file.
- Saving keys does not send a Gemini request or consume quota.
- Taskloom uses the primary key first. It tries the backup only after a Gemini 429/rate-limit response.
- If Google returns a 429 project-quota error, check your project's **active rate limits** in Google AI Studio. Taskloom's local daily counter is not Google's quota.
- The desktop build defaults to `gemini-3.1-flash-lite` through Gemini's standard `generateContent` API. It retries temporary 503/504 capacity errors a limited number of times; it does not repeatedly retry quota-exhausted 429s.
- Never share API keys in screenshots, chat messages, or source control.

## Why Taskloom instead of Gemini directly?

Gemini is the model that generates or validates the structured result. Taskloom is the workflow layer around it:

| Gemini directly | Taskloom |
| --- | --- |
| One prompt to one model response | One request is normalized, planned, reviewed, and presented as a traceable workflow |
| Internal process is largely opaque | Shows intent, constraints, assigned logical roles, review score, and output trace |
| You manage retries and quotas manually | Uses local caching, request accounting, and a primary/backup 429 failover path |
| Output only | Output plus a human-readable agent map, language trace, and quality review |

Taskloom also includes an optional **Gemini comparison** tab. It sends the same request through a direct, one-response Gemini baseline and places both outputs side by side with transparent local measurements. The baseline is opt-in because it can use one additional API request.

The v2 interface uses a dark cobalt theme and preserves unfinished prompts and revision notes while navigating between pages. The local History page saves completed requests on this PC without saving API keys.

The named “agents” are logical Python roles coordinated by the application. Gemini is called once for the configured provider path; Taskloom then reconstructs and presents the specialist workflow locally. This makes the demonstration transparent without claiming that Gemini exposes its private chain of thought.

## Workflow

```text
User request
    ↓
Python normalization + intent/entity/constraint analysis
    ↓
Planner creates dependent logical tasks and specialist roles
    ↓
Gemini provider (or local mock provider) produces validated structured material
    ↓
Python reviewer checks the material and assembles the visible trace
    ↓
Preview → revise or approve → download content
```

### Logical roles

1. **Language Understanding Agent** — extracts intent, entities, constraints, and ambiguity.
2. **Planner Agent** — decomposes the request into focused tasks and assigns roles.
3. **Worker Agent pool** — prepares specialist material.
4. **Reviewer Agent** — evaluates the material and reports a visible score.
5. **NLG Writer Agent** — synthesizes approved material into the final preview.

The **Coordinator** is deterministic Python orchestration, not a separate model call.

## Tech stack

- **Python + Streamlit** — application logic and interface.
- **pywebview** — displays the local app in a native Windows window; no external browser is required for the desktop build.
- **google-genai** — Gemini API client.
- **Pydantic** — validates structured request and response data.
- **keyring** — saves personal API keys in Windows Credential Manager.
- **diskcache** — local response cache, reducing repeated API usage.
- **ReportLab** — PDF content export.
- **PyInstaller** — packages both the app and the one-file Windows installer.

## Development

```powershell
# Install dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-build.txt

# Run the app in development mode
.\.venv\Scripts\streamlit.exe run app.py

# Test
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# Build the native app
.\build_windows_exe.ps1

# Build the clean, one-file Windows installer
.\build_windows_installer.ps1
```

The installer output is:

```text
Taskloom Installer\Taskloom Setup.exe
```

`Taskloom Setup.exe` is intentionally distributed separately from development output. Do not commit `.env`, Windows credentials, caches, `dist`, or `build` artifacts.

## Mock mode

Taskloom can demonstrate its full interface without an API key in mock mode. For development only, copy `.env.example` to `.env` and set provider-related values as needed. Never commit `.env`.
