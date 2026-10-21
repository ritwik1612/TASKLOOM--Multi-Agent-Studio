# ✦ Taskloom — Multi-Agent Studio

### One request. Many specialist roles. One reviewable result.

Taskloom is a native Windows application that makes AI-assisted language work more structured, inspectable, and human-controlled. Instead of presenting a response as a black box, it turns a request into a visible workflow: understand the request, plan specialised work, generate material, review it, and present a final result for approval or revision.

> **Built for demonstrations, learning, and thoughtful AI-assisted content work.**

> **Download the app from [Releases](https://github.com/ritwik1612/TASKLOOM--Multi-Agent-Studio/releases/latest). Do not use GitHub’s “Code → Download ZIP”; that archive is for source code, not installation.**

---

## What Taskloom does

| Capability | What you can see |
| --- | --- |
| **Request understanding** | Normalised request, detected intent, entities, constraints, and ambiguity |
| **Task planning** | Logical subtasks and the specialist roles assigned to them |
| **Structured generation** | An organised preview rather than an unstructured response alone |
| **Quality review** | A visible review score and revision path before you finalise content |
| **Traceability** | Agent map, language trace, communication trace, and quality review panels |
| **Human control** | Approve, revise, download, or return to the task at every important stage |

---

## Taskloom vs. using Gemini directly

Gemini is the language model that can generate or validate material. Taskloom is the application and workflow layer around that capability.

| Using Gemini directly | Using Taskloom |
| --- | --- |
| You submit a prompt and receive a response | You submit one request and receive a planned, reviewable workflow plus the response |
| The transformation process is mostly opaque | Intent, constraints, logical roles, task assignments, and review outcomes are displayed |
| One general interaction | Structured specialist roles such as understanding, planning, worker, reviewer, and writer |
| You must manage repeated requests and rate limits yourself | Local caching, local request accounting, clear quota errors, and bounded retries for temporary provider failures |
| Final text is the primary output | Final text plus an agent map, language trace, review record, and revision controls |

Taskloom does **not** claim access to Gemini’s private reasoning. Its visible traces describe Taskloom’s own Python-managed workflow and validated structured output.

The optional **Gemini comparison** tab sends the same request through a direct, one-response Gemini baseline, then presents both outputs side by side with deterministic local measurements. It is deliberately opt-in because it may use one additional API request. Taskloom keeps a dark cobalt interface and preserves unfinished prompts and revision notes while you navigate between pages.

---

## From request to result

```text
YOUR REQUEST
     │
     ▼
Language Understanding
intent · entities · constraints · ambiguity
     │
     ▼
Planner
logical subtasks · specialist roles · dependencies
     │
     ▼
Gemini or local mock provider
validated structured material
     │
     ▼
Python review and synthesis
quality check · visible trace · final preview
     │
     ▼
APPROVE · REVISE · DOWNLOAD CONTENT
```

### Logical specialist roles

1. **Language Understanding Agent** — interprets the request and its language constraints.
2. **Planner Agent** — creates a non-redundant task plan and assigns roles.
3. **Worker Agent pool** — prepares role-specific material.
4. **Reviewer Agent** — checks the material before it reaches the final preview.
5. **NLG Writer Agent** — synthesises approved material into clear output.

The coordinator is deterministic Python orchestration. The role names represent structured application stages, not separate paid API calls.

---

## Install Taskloom on Windows

1. Open [Releases](https://github.com/ritwik1612/TASKLOOM--Multi-Agent-Studio/releases/latest) and download **`Taskloom Setup.exe`** from the v2 release.
2. Double-click **`Taskloom Setup.exe`**.
3. Approve the Windows prompt. The default location is **`C:\Program Files\Taskloom`**.
4. Keep the default or choose **Browse** to install somewhere else.
5. Leave **Open Taskloom when installation finishes** selected to begin immediately.

No command line, Python installation, or development setup is needed for normal use.

After installation, search the Windows Start menu for **Taskloom**. The installer creates a Start-menu shortcut automatically.

The v2 interface includes a logo-opened navigation menu, a local History page, dedicated workflow and architecture views, and a layout that adapts to narrow windows. History is stored only on this PC under `%LOCALAPPDATA%\Taskloom\history`; it does not contain your API keys. The installer is for Windows, while the responsive layout can also be previewed in a phone browser during development.

### Download generated content

After approving an output, choose **Download content** and select Markdown, plain text, or PDF. The desktop app writes the file directly to your Windows **Downloads** folder. If a file with the same name already exists, Taskloom creates a numbered copy instead of overwriting it.

---

## Connect Gemini securely

1. In Taskloom, choose **Connect Gemini**.
2. Select **Open Google AI Studio** and create your own Gemini API key.
3. Paste it as the **primary key**.
4. Optionally add a separate **backup key** for continuity.
5. Select **Save securely and connect**.

### Key and rate-limit behaviour

| Situation | Taskloom behaviour |
| --- | --- |
| Normal request | Uses your primary Gemini key |
| Primary key receives Gemini 429 | Tries the backup key once |
| Both keys receive 429 | Clearly reports the rate limit instead of silently cycling keys |
| Exact repeated request | Can be served from the local cache without a new Gemini call |
| Save key | Stores it in **Windows Credential Manager**; saving itself does not use quota |

The default model is `gemini-3.1-flash-lite`, called through Gemini's standard `generateContent` API. An initial preview normally uses one successful model response; temporary 503/504 capacity failures may be retried up to two times. A 429 project-quota error is not repeatedly retried. **Two API keys from the same Google project share that project's quota**, so a backup key only provides independent quota if it belongs to a different eligible project. Taskloom's local daily budget is not your live Google quota—check your project's active limits in [Google AI Studio](https://aistudio.google.com/rate-limit).

Never share your API keys in screenshots, messages, or repositories. Taskloom does not store them in this project folder.

---

## Repository guide

| Item | Purpose |
| --- | --- |
| **`Taskloom Setup.exe`** | The only file most users need — the Windows installer |
| **`START HERE.txt`** | A short plain-text installation guide |
| **`Source Code`** | Application source, visual assets, tests, and packaging material for reviewers/developers |

---

## Technology at a glance

Taskloom is built with **Python**, **Streamlit**, and **pywebview** to provide a native Windows window. It uses **google-genai** for the optional Gemini connection, **Pydantic** for structured-data validation, **keyring** for secure Windows Credential Manager storage, **diskcache** for local caching, and **ReportLab** for PDF content export.

<p align="center"><i>Taskloom · Multi-Agent Language Studio</i></p>
