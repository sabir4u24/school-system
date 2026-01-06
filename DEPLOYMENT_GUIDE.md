# Deployment Guide: Koyeb + Aiven (Free Tier)

This guide will walk you through deploying your School Management System for free using **GitHub** (code storage), **Aiven** (Database), and **Koyeb** (Hosting).

## Prerequisites
1.  **GitHub Account**: [Sign up here](https://github.com/join)
2.  **Koyeb Account**: [Sign up here](https://app.koyeb.com/auth/signup)
3.  **Aiven Account**: [Sign up here](https://console.aiven.io/signup)
4.  **Git Installed**: You need `git` on your computer.

---

## Step 1: Push Code to GitHub

You need to upload your code to a repository.

1.  **Initialize Git** (if you haven't already):
    ```bash
    git init
    git add .
    git commit -m "Initial commit for deployment"
    ```
2.  **Create a Repo on GitHub**:
    *   Go to [github.com/new](https://github.com/new).
    *   Name it `school-system`.
    *   **Do NOT** check "Add a README" or .gitignore (we already made one).
    *   Click **Create repository**.
3.  **Push your code**:
    *   Copy the commands shown under "…or push an existing repository from the command line".
    *   They look like this (replace `YOUR_USERNAME`):
    ```bash
    git branch -M main
    git remote add origin https://github.com/YOUR_USERNAME/school-system.git
    git push -u origin main
    ```

---

## Step 2: Set up Database (Aiven)

1.  Log in to [Aiven Console](https://console.aiven.io/).
2.  Click **Create Service**.
3.  Select **MySQL**.
4.  Select **Cloud**: Choose `Google Cloud` or `AWS` (doesn't matter much).
5.  Select **Region**: Choose one close to you (e.g., `asia-south1` if available).
6.  Select **Plan**: Choose **Free** (Micro).
7.  Give it a name (e.g., `school-db`) and click **Create Service**.
8.  Wait for it to show "Running" (green dot).
9.  Copy the **Service URI**. It looks like:
    `mysql://avnadmin:password@host:port/defaultdb?ssl-mode=REQUIRED`

---

## Step 3: Deploy to Koyeb

1.  Log in to [Koyeb](https://app.koyeb.com/).
2.  Click **Create App**.
3.  Select **GitHub** as the source.
4.  Select your `school-system` repository.
5.  **Builder**: Leave as `Buildpack` (Python should be auto-detected).
6.  **Environment Variables**:
    You MUST add the following variables so the app knows how to connect to the DB.
    *   Click **Add Variable**.
    *   `DATABASE_URL` = Paste your Aiven Service URI here.
    *   `DJANGO_SECRET_KEY` = Type a long random string (e.g., `unsafe-secret-change-me-12345`).
    *   `DEBUG` = `False`
7.  Click **Deploy**.

---

## Step 4: Final Configuration

Once the deployment finishes and shows "Healthy":

### 1. Run Migrations
Your database is empty. You need to create the tables.
1.  In Koyeb, go to your Service.
2.  Click **Console** (or "Instance" > "Console").
3.  Type this command and hit Enter:
    ```bash
    python manage.py migrate
    ```

### 2. Create Superuser
To access the admin panel:
1.  In the same Console, type:
    ```bash
    python manage.py createsuperuser
    ```
2.  Follow the prompts to set username/password.

### 3. Visit your Site
Click the **Public URL** (ends in `.koyeb.app`) provided by Koyeb. Login with your superuser account!

---

## Important Note on Media Files
On free hosting platforms like Koyeb, the filesystem is **ephemeral**. This means any **Student Photos** you upload will **disappear** if the app restarts or redeploys.

To fix this for production, you would typically use **AWS S3** or **Cloudinary** to store images. That requires extra setup. For now, understand that text data (Names, Marks) is safe in the database, but uploaded images are temporary.
