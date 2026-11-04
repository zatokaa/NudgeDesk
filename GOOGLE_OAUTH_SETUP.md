# Google Cloud OAuth 2.0 Setup Guide for NudgeDesk

This guide provides step-by-step instructions for creating and configuring your Google Cloud Console credentials to enable two-way synchronization between **NudgeDesk** and your **Google Tasks** account.

---

## Step 1: Create a Project in Google Cloud Console

1. Open your web browser and navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2. Sign in with your Google account.
3. In the top navigation bar, click the project dropdown (next to the "Google Cloud" logo) and click **New Project**.
4. Set the project details:
   - **Project Name:** `NudgeDesk` (or any name you prefer)
   - **Organization:** Select *No organization* (or your Google Workspace org if applicable)
5. Click **Create** and wait a few seconds until the project is created, then select it from the project dropdown.

---

## Step 2: Enable the Google Tasks API

1. In the Google Cloud Console, open the left navigation menu (☰) and select **APIs & Services** > **Library**.
2. In the search box, search for: `Tasks API` or `Google Tasks API`.
3. Click on **Google Tasks API**.
4. Click the blue **Enable** button.

*(Optional but recommended)*: Also search for and enable the **Google People API** or **OAuth2 API** if you want NudgeDesk to automatically fetch your profile name and email avatar.

---

## Step 3: Configure the OAuth Consent Screen

Before generating credentials, Google requires an OAuth consent screen:

1. In the left navigation menu, navigate to **APIs & Services** > **OAuth consent screen**.
2. Select **User Type**:
   - If using a personal `@gmail.com` account: select **External** and click **Create**.
   - If using Google Workspace: you may choose **Internal** or **External**.
3. Fill in the **App Information**:
   - **App name:** `NudgeDesk`
   - **User support email:** Select your Google email address.
   - **Developer contact information:** Enter your email address.
   - Click **Save and Continue**.
4. **Scopes:**
   - Click **Add or Remove Scopes**.
   - Filter or locate: `https://www.googleapis.com/auth/tasks` (Create, edit, organize, and delete all your tasks).
   - Check the box and click **Update**.
   - Click **Save and Continue**.
5. **Test Users** *(Crucial for personal accounts)*:
   - Because your app is in "Testing" mode, Google will only allow authorized test users to sign in.
   - Click **+ Add Users**.
   - Enter your Google email address (and any family or team members who will use the app).
   - Click **Add**, then **Save and Continue**.
6. Review the summary and return to the dashboard.

---

## Step 4: Create OAuth 2.0 Client ID

1. In the left navigation menu, go to **APIs & Services** > **Credentials**.
2. At the top of the screen, click **+ Create Credentials** and select **OAuth client ID**.
3. Configure the credential:
   - **Application type:** Select **Desktop app**.
   - **Name:** `NudgeDesk Desktop Client`
4. Click **Create**.
5. A modal will appear showing *OAuth client created*. Click **Download JSON** (or close and click the Download icon ⬇️ next to your client in the list).
6. Save this file to your computer. It is usually named something like `client_secret_xxxxxxxxxx.json`. Rename it to:
   ```
   credentials.json
   ```

---

## Step 5: Connect NudgeDesk

You have two convenient ways to connect your credentials:

### Method A: Through NudgeDesk UI (Recommended)
1. Launch **NudgeDesk**.
2. In the sidebar, click **⚙️ Settings**.
3. Under **Google Tasks Integration**, click the button: **Load credentials.json**.
4. Select your downloaded `credentials.json` file.
5. Click **Sign In with Google**.
6. Your default web browser will automatically open:
   - Sign in to your Google Account.
   - If you see a *"Google hasn't verified this app"* warning screen, click **Advanced** > **Go to NudgeDesk (unsafe)** (this is expected for private desktop apps in developer mode).
   - Check the permission to manage tasks and click **Continue**.
7. The browser tab will say *"Authentication successful! You can now close this tab and return to NudgeDesk."*
8. NudgeDesk will immediately switch to **Synced** state, showing your connected email and downloading all your Google Tasks and lists!

### Method B: Manual File Placement
Place the `credentials.json` file directly into:
- The same folder as `NudgeDesk.exe` (or `main.py`), or
- `%APPDATA%\NudgeDesk\credentials.json`

---

## Step 6: Security and Token Storage

- NudgeDesk **never** sees or stores your Google password.
- Authentication tokens (`access_token` and `refresh_token`) are securely stored in the **Windows Credential Manager** (or encrypted via **Windows DPAPI** tied to your current Windows user login).
- When you click **Sign Out** in Settings, the tokens are wiped from your machine.

---

## Troubleshooting

- **Error 403: access_denied / App has not completed Google verification:**
  Make sure your Google email address is added under **Test Users** on the *OAuth consent screen* page in Google Cloud Console.
- **Token expired:**
  NudgeDesk automatically uses your secure refresh token to obtain a fresh access token without interrupting your workflow. If you ever revoke access from your Google Account settings, simply click **Sign Out** and **Sign In with Google** again.

