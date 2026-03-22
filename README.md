# 📸 SmaPasha (スマパシャ)

**Right-click long press → Instant screenshot. No keyboard needed.**

**右クリック長押し → 即スクショ。キーボード不要。**

---

## 🎬 Demo / デモ

> *▶️ [Demo video on X (Twitter)](https://x.com/all_in_one_mite)*

---

## ⚠️ Important: Snipping Tool Prerequisite / 前提条件

**EN:** SmaPasha uses Windows built-in Snipping Tool internally. It is recommended to **uninstall the default Snipping Tool** and use the **Preview version** instead. If you don't use Snipping Tool for video recording, we recommend removing it before use. You can always reinstall it from the [Microsoft Store](https://apps.microsoft.com/detail/9MZ95KL8MR0L).

**JP:** スマパシャはWindows標準の「Snipping Tool（切り取り領域とスケッチ）」を内部で呼び出して動作しています。既存のSnipping Toolを**アンインストール**し、**プレビュー版**をご使用ください。Snipping Toolで動画撮影をしない方は、削除してからお使いください。[Microsoft Store](https://apps.microsoft.com/detail/9MZ95KL8MR0L)からいつでも再ダウンロードできます。

---

## 📁 Which file to use? / どっちを使う？

| File | OS | Description |
|---|---|---|
| `main.pyw` | **Windows 11** | Standard version / 標準版 |
| `main_win10.pyw` | **Windows 10** | Includes CF_HDROP clipboard fix for Win10 Snipping Tool / Win10のSnipping Tool用クリップボード修正付き |

**EN:** Windows 10's Snipping Tool doesn't automatically set the screenshot as a file in the clipboard. The Win10 version adds `set_clipboard_file()` to handle this, so you can paste screenshots as files just like on Win11.

**JP:** Win10のSnipping Toolはスクショをファイルとしてクリップボードにセットしません。Win10版では`set_clipboard_file()`を追加して、Win11と同じようにファイルとして貼り付けできるようにしています。

---

## What is SmaPasha? / スマパシャとは？

**EN:** SmaPasha lets you invoke Windows Snipping Tool by simply long-pressing the right mouse button (0.2 sec). No keyboard shortcut needed — your hand stays on the mouse the entire time. Screenshots are automatically saved to your chosen folder. It also includes AI-powered auto-rename using Google Gemini.

**JP:** スマパシャは、マウスの右クリックを0.2秒長押しするだけでSnipping Toolを起動できるWindowsツールです。キーボードショートカット不要 — 手はマウスに乗ったまま。スクショは指定フォルダに自動保存されます。Google GeminiによるAI自動リネーム機能もあります。

---

## Why? / なぜ作ったか

**EN:** If you use AI tools like ChatGPT or Claude, you know — you're constantly screenshotting. Every few minutes, stop, move hand to keyboard, Win+Shift+S, back to mouse. SmaPasha eliminates this friction completely.

**JP:** ChatGPTやClaudeみたいなAIツールを使ってると、スクショを何度も撮る場面がある。そのたびにWin+Shift+Sで手を止めるのは地味にストレス。スマパシャはその摩擦をゼロにします。

---

## Features / 機能

| Feature | Description |
|---|---|
| 🖱️ Right-click long press | Invoke Snipping Tool without touching the keyboard / キーボードなしでSnipping Tool起動 |
| 💾 Auto-save | Screenshots saved to your chosen folder automatically / 指定フォルダに自動保存 |
| 📋 Clipboard ready | Screenshot is also copied to clipboard for instant paste / クリップボードにもコピーされペースト可能 |
| 🤖 AI rename (optional) | Gemini AI analyzes the image and names the file for you / AIが画像内容からファイル名を自動生成 |
| 📝 Manual rename | Prefix + sequential numbering / プレフィックス＋連番 |
| 🚫 App exclusion | Skip capture for specific apps (e.g. Honeyview) / 除外アプリ指定可能 |
| ⚡ Zero learning curve | Right-click is all you need to know / 覚える操作は右クリックだけ |

---

## Requirements / 必要なもの

- **Windows 10 / 11** (Snipping Tool required)
- **Python 3.8+**
- Libraries / ライブラリ:
  - `pynput`
  - `Pillow`
  - `python-dotenv`
  - `google-genai` (only for AI rename / AIリネーム使用時のみ)

---

## Installation / インストール

```bash
git clone https://github.com/YOUR_USERNAME/smapasha.git
cd smapasha
pip install pynput Pillow python-dotenv google-genai
```

---

## Usage / 使い方

```bash
# Windows 11
python main.pyw

# Windows 10
python main_win10.pyw
```

Or just double-click `main.pyw` (Win11) or `main_win10.pyw` (Win10).

1. **Launch** — A small settings window appears / 小さい設定画面が表示される
2. **Right-click long press (0.2 sec)** — Snipping Tool pops up / Snipping Toolが起動
3. **Select area** — Screenshot is auto-saved and copied to clipboard / スクショが自動保存＆クリップボードにコピー

---

## AI Rename Setup (Optional) / AIリネーム設定（任意）

The AI rename feature uses Google Gemini to automatically name your screenshots based on their content.

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and create an API key
2. Create a `.env` file in the same folder as `main.pyw`
3. Add your key:

```
GEMINI_API_KEY=your_api_key_here
```

4. Restart SmaPasha

---

## Building .exe / EXE化

To share with people who don't have Python:

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile main.pyw
```

The `.exe` will be in the `dist` folder.

---

## Feature Request / 機能提案

I've submitted a feature request to Microsoft to add this right-click long press functionality to Snipping Tool natively. If you find SmaPasha useful, please upvote!

🗳️ **English:** [Upvote on Feedback Hub](https://aka.ms/AA109ahh) (Opens in Feedback Hub on PC)

🗳️ **日本語:** [Feedback Hubで投票](https://aka.ms/AA10a6ad) (PCのFeedback Hubで開きます)

---

## How it works / 仕組み

```
Right-click held 0.2sec → ESC burst (suppress context menu) → Win+Shift+S sent → Snipping Tool opens
→ User selects area → Clipboard monitored → Auto-save to folder → (Optional) AI rename
```

---

## License

MIT

---

## Author

**yoshida** — [X (Twitter)](https://x.com/all_in_one_mite)

Built with Claude Code. 300+ hours of AI-powered development.
