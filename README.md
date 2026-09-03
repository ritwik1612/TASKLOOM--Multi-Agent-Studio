# Taskloom Desktop

## Install Taskloom

1. Double-click **`Taskloom Setup.exe`** in this folder.
2. Approve the Windows prompt. This lets Taskloom install to its default location: **`C:\Program Files\Taskloom`**.
3. Keep that location or select **Browse** to choose your own folder.
4. Leave **Open Taskloom when installation finishes** selected if you want to start immediately.

That is all you need to install the app. No command line, Python installation, or setup files are required.

## Connect Gemini on first use

1. In Taskloom, select **Connect Gemini**.
2. Select **Open Google AI Studio**.
3. Create your own Gemini API key and paste it as the **primary key**.
4. Optionally add a separate backup key. It is used only if Gemini rate-limits the primary key with a 429 response.
5. Select **Save securely and connect**.

Your keys are stored only in **Windows Credential Manager**. They are not kept in this folder or uploaded to this repository.

## Folder guide

- **`Taskloom Setup.exe`** — the only file most users need.
- **`START HERE.txt`** — the same short installation guide in plain text.
- **`Source Code`** — project code and build material, kept separate for developers and reviewers.

## What is Taskloom?

Taskloom is a reviewable multi-agent language-processing studio. It takes one request, maps its intent and constraints, assigns logical specialist roles, generates an output with Gemini, and presents the resulting workflow for you to inspect.
