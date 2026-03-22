import tkinter as tk
from tkinter import filedialog
from pynput import mouse, keyboard
from PIL import ImageGrab, Image
import time
import os
import threading
from datetime import datetime
import winsound
import ctypes
from dotenv import load_dotenv
import queue
import traceback

# .envファイルの読み込み
load_dotenv()

# Gemini AIクライアントの準備
gemini_client = None
try:
    from google import genai
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        gemini_client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"Gemini API初期化エラー: {e}")

# グローバル状態
import json

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"設定の読み込みエラー: {e}")
    return {}

def load_save_dir():
    data = load_config()
    save_dir = data.get("save_dir")
    if save_dir and os.path.isdir(save_dir):
        return save_dir
    return os.path.join(os.path.expanduser("~"), "Desktop")

def save_config(save_dir=None, rename_mode=None):
    data = load_config()
    if save_dir is not None:
        data["save_dir"] = save_dir
    if rename_mode is not None:
        data["rename_mode"] = rename_mode
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"設定の保存エラー: {e}")

app_enabled = True
default_save_dir = load_save_dir()

# 手動リネーム用の連番カウンター
manual_rename_counter = 1

# リネームモード: 'manual' / 'ai' / 'off'
rename_mode = load_config().get("rename_mode", "ai")

# 互換性のために別名で参照も定義
ai_rename_enabled = (rename_mode == "ai")
manual_rename_enabled = (rename_mode == "manual")

# 長押しと判定する秒数（コンテキストメニューが出ないようにやや遅めの0.25秒へ微調整）
LONG_PRESS_THRESHOLD = 0.2
# キャプチャ待機状態フラグ
capture_ready = False
# 右クリックが押された時間
right_click_start_time = 0
# 長押し検知タイマー
capture_timer = None

# --- 除外アプリリスト（ウィンドウタイトルに含まれる文字列） ---
EXCLUDE_APPS = ["Honeyview"]

# キーボードコントローラ
keyboard_controller = keyboard.Controller()

# クリップボードを一旦空にするためのヘルパー
def clear_clipboard():
    try:
        ctypes.windll.user32.OpenClipboard(0)
        ctypes.windll.user32.EmptyClipboard()
        ctypes.windll.user32.CloseClipboard()
        return True
    except Exception as e:
        print(f"クリップボードのクリアに失敗: {e}")
        return False

def auto_rename_image_with_ai(filepath):
    """
    保存された画像をAIに解析させ、内容に基づいた名前にリネームする
    """
    global gemini_client
    if not gemini_client:
        print("Gemini APIクライアントが有効ではありません。リネームをスキップします。")
        return
        
    try:
        print(f"🤖 AIが画像の内容を解析中... ({filepath})")
        
        # 該当画像を開く
        img = Image.open(filepath)
        
        # AIへの指示プロンプト
        prompt = (
            "この画像の内容を端的に表す短いファイル名を日本語で1つだけ生成してください。"
            "拡張子（.pngなど）は不要です。"
            "空白や記号（\\/:*?\"<>|等）は絶対に含めず、できるだけ具体的でわかりやすい名前にしてください。"
            "例：コマンドプロンプトのエラー画面、VRチャットの集合写真、Pythonのコード解説、など。"
            "必ずファイル名として使える文字だけで、名前のテキストのみを出力してください。"
        )
        
        # 最新の3.0から順に、確実に動くモデルを探して片っ端から試す必勝フォールバック
        models_to_try = ['gemini-3.0-flash', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
        response = None
        for model_name in models_to_try:
            try:
                response = gemini_client.models.generate_content(
                    model=model_name,
                    contents=[img, prompt]
                )
                print(f"✅ AIモデル {model_name} でリネームに成功しました！")
                break
            except Exception as e:
                print(f"⚠️ {model_name} は使用できませんでした。次のバージョンを試します...")
        
        # リネーム前にお作法としてファイルを閉じる（Windowsでのファイルロックエラー回避）
        img.close()
        
        if not response:
            print("すべてのGeminiモデルがエラーになりました。APIキーかネットワークを確認してください。")
            return
            
        suggested_name = response.text.strip()
        
        # 念のためWindowsのファイル名に使えない文字を除去
        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|', '\n', '\r', ' ',"　"]
        for char in invalid_chars:
            suggested_name = suggested_name.replace(char, '_')
            
        if not suggested_name:
            print("AIからの応答が空でした。リネームをスキップします。")
            return
            
        dir_name = os.path.dirname(filepath)
        new_filepath = os.path.join(dir_name, f"{suggested_name}.png")
        
        # 同名ファイルがある場合は連番をつける
        counter = 1
        while os.path.exists(new_filepath):
            new_filepath = os.path.join(dir_name, f"{suggested_name}_{counter}.png")
            counter += 1
            
        # ファイル名を変更
        # ファイルがまだ書き込みロックされている可能性があるので少し待つ
        time.sleep(0.5)
        os.rename(filepath, new_filepath)
        print(f"✨ AIによる自動リネーム成功！\n【変更前】{os.path.basename(filepath)}\n【変更後】{os.path.basename(new_filepath)}")
        
    except Exception as e:
        print(f"AI自動リネーム中にエラーが発生しました: {e}")

def watch_clipboard_and_save():
    """
    Snipping Tool起動後、クリップボードに画像がコピーされるのを監視して保存する
    """
    print("クリップボードの監視を開始します...")
    # タイムアウト時間（秒）
    timeout = 30
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # クリップボードから画像を取得
            img_data = ImageGrab.grabclipboard()
            
            if img_data is not None:
                img = None
                # Snipping Toolの仕様により、画像本体ではなく画像ファイルのパスのリストになる場合がある
                if isinstance(img_data, list):
                    if len(img_data) > 0:
                        print(f"クリップボードにファイルパスを発見しました: {img_data[0]}")
                        try:
                            img = Image.open(img_data[0])
                        except Exception as e:
                            print(f"画像の読み込みに失敗しました: {e}")
                else:
                    print("クリップボードに画像データ本体を発見しました！")
                    img = img_data
                
                if img is not None:
                    # 保存先パスの取得
                    target_dir = save_dir_var.get()
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                        
                    # ファイル名決定
                    global manual_rename_counter
                    prefix_text = manual_prefix_var.get().strip() if rename_mode == "manual" else ""
                    if prefix_text:
                        filename = f"{prefix_text}_{manual_rename_counter:03d}.png"
                        manual_rename_counter += 1
                        # 同名ファイルがあれば連番をずらす
                        filepath_candidate = os.path.join(target_dir, filename)
                        while os.path.exists(filepath_candidate):
                            filename = f"{prefix_text}_{manual_rename_counter:03d}.png"
                            manual_rename_counter += 1
                            filepath_candidate = os.path.join(target_dir, filename)
                        filename = os.path.basename(filepath_candidate)
                    else:
                        filename = f"Capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    filepath = os.path.join(target_dir, filename)
                    
                    # PNGとして保存
                    # imgオブジェクトによっては直接saveできない場合があるので、RGBに変換する
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(filepath, 'PNG')
                    print(f"✅ 保存完了: {filepath}")
                    

                    # AIリネーム：モードが'ai'の時のみ
                    if rename_mode == "ai":
                        threading.Thread(target=auto_rename_image_with_ai, args=(filepath,), daemon=True).start()
                    
                    # リョウの要望により、貼り付け（ペースト）できるようにクリップボードはクリアしない！
                    return # 監視終了
                
        except Exception as e:
            print(f"クリップボードチェック中のエラー: {e}")
            
        # 1秒おきにチェック
        time.sleep(1)
        
    print("タイムアウト：クリップボードに画像がコピーされませんでした。")

def launch_snipping_tool():
    """
    Win + Shift + S を送信して Snipping Tool を起動する
    """
    print("📸 Snipping Tool を起動します...")
    
    # 古い画像が残っていると間違えて保存しちゃうので、事前にクリップボードを空にする
    clear_clipboard()
    
    # 実際にキーボードからショートカットを入力しているように振る舞う
    with keyboard_controller.pressed(keyboard.Key.cmd):
        with keyboard_controller.pressed(keyboard.Key.shift):
            keyboard_controller.press('s')
            keyboard_controller.release('s')
            
    # 少し待ってからクリップボードの監視をバックグラウンドで開始
    time.sleep(1)
    threading.Thread(target=watch_clipboard_and_save, daemon=True).start()

def set_capture_ready():
    """タイマーから呼ばれるキャプチャ準備完了関数"""
    global capture_ready
    capture_ready = True
    print("長押し到達！離した瞬間にSnipping Toolを呼び出します！")

def is_excluded_app_active():
    """現在アクティブなウィンドウが除外リストに含まれているか判定"""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        
        # 1. ウィンドウタイトルで判定
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        active_title = buff.value.lower()
        for app in EXCLUDE_APPS:
            if app.lower() in active_title:
                return True
                
        # 2. プロセス(exe)名で判定
        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        h_process = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if h_process:
            exe_path = ctypes.create_unicode_buffer(260)
            size = ctypes.c_ulong(260)
            if ctypes.windll.kernel32.QueryFullProcessImageNameW(h_process, 0, exe_path, ctypes.byref(size)):
                exe_name = os.path.basename(exe_path.value).lower()
                for app in EXCLUDE_APPS:
                    if app.lower() in exe_name:
                        ctypes.windll.kernel32.CloseHandle(h_process)
                        return True
            ctypes.windll.kernel32.CloseHandle(h_process)
    except Exception as e:
        print(f"除外判定エラー: {e}")
    return False

def on_mouse_event(x, y, button, pressed):
    """
    マウスのクリックイベントを監視
    """
    global app_enabled, capture_timer, right_click_start_time, capture_ready
    
    if not app_enabled:
        return
        
    if button == mouse.Button.right:
        if pressed:
            # アクティブウィンドウが除外リスト（Honeyviewなど）なら何もしない
            if is_excluded_app_active():
                return
            
            # 押した瞬間にタイマーセット
            capture_ready = False
            right_click_start_time = time.time()
            if capture_timer is None:
                capture_timer = threading.Timer(LONG_PRESS_THRESHOLD, set_capture_ready)
                capture_timer.start()
        else:
            # 離された時、タイマーをキャンセル
            if capture_timer is not None:
                capture_timer.cancel()
                capture_timer = None
            
            # 長押し判定が完了していたら、離した瞬間にキャプチャ起動
            if capture_ready:
                def delayed_capture():
                    # 右クリック離し直後に出る右クリックメニューをキャンセル
                    # プログラムが軽快すぎると、OSがメニューを描画する「前」にESCを送って無効化されている可能性があるため
                    # ほんの少しだけ（0.015秒）意図的に「タメ」を作る
                    time.sleep(0.015)
                    
                    # そこから怒涛のESC連打（0.02秒間隔で8連打、計0.16秒カバー）
                    for _ in range(8):
                        keyboard_controller.press(keyboard.Key.esc)
                        keyboard_controller.release(keyboard.Key.esc)
                        time.sleep(0.02)

                    # 少し待ってからSnipping Toolを起動
                    time.sleep(0.15)
                    launch_snipping_tool()
                    
                threading.Thread(target=delayed_capture, daemon=True).start()
                capture_ready = False

            right_click_start_time = 0

def toggle_app():
    global app_enabled
    app_enabled = not app_enabled
    
    if app_enabled:
        status_label.config(text="状態: ON (長押し監視中👀)", fg="#2e7d32")
        toggle_btn.config(text="OFFにする", bg="#4CAF50", fg="white")
    else:
        status_label.config(text="状態: OFF", fg="#c62828")
        toggle_btn.config(text="ONにする", bg="#f44336", fg="white")


# --- リネームモードの切り替え（ラジオボタン方式）
def set_rename_mode(mode):
    """mode: 'manual' / 'ai' / 'off'"""
    global rename_mode
    rename_mode = mode
    save_config(rename_mode=mode)
    # ボタンの色を更新（押されたボタン=凹む、他=グレー）
    if mode == "manual":
        btn_manual.config(bg="#e65100", fg="white", relief="sunken")
        btn_ai.config(bg="#bdbdbd", fg="#555", relief="raised")
        btn_off.config(bg="#bdbdbd", fg="#555", relief="raised")
    elif mode == "ai":
        btn_manual.config(bg="#bdbdbd", fg="#555", relief="raised")
        btn_ai.config(bg="#1565c0", fg="white", relief="sunken")
        btn_off.config(bg="#bdbdbd", fg="#555", relief="raised")
    else:  # off
        btn_manual.config(bg="#bdbdbd", fg="#555", relief="raised")
        btn_ai.config(bg="#bdbdbd", fg="#555", relief="raised")
        btn_off.config(bg="#c62828", fg="white", relief="sunken")

def choose_directory():
    root.attributes('-topmost', False)
    selected_dir = filedialog.askdirectory(initialdir=save_dir_var.get(), title="保存先フォルダを選択")
    if selected_dir:
        save_dir_var.set(selected_dir)
    root.attributes('-topmost', True)

# ==========================================
# GUI セットアップ (tkinter)
# ==========================================
root = tk.Tk()
root.title("Snipping連携・長押しキャプチャ")
root.attributes('-topmost', True)
root.geometry("480x420")
root.resizable(False, False)

title_label = tk.Label(root, text="✂️ マウス右長押しキャプチャ (Snipping連携)", font=("Meiryo", 14, "bold"))
title_label.pack(pady=(15, 5))

status_label = tk.Label(root, text="状態: ON (長押し監視中👀)", fg="#2e7d32", font=("Meiryo", 14, "bold"))
status_label.pack(pady=5)

toggle_btn = tk.Button(root, text="OFFにする", command=toggle_app, font=("Meiryo", 12, "bold"), bg="#4CAF50", fg="white", width=20, height=1)
toggle_btn.pack(pady=10)

# バツで閉じた時は尞に機能をOFFにする
def on_close():
    global app_enabled
    app_enabled = False
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

save_frame = tk.Frame(root)
save_frame.pack(pady=5, fill=tk.X, padx=20)

tk.Label(save_frame, text="📁 画像の保存先パス：", font=("Meiryo", 10, "bold")).pack(anchor=tk.W)

save_dir_var = tk.StringVar(value=default_save_dir)

def on_save_dir_change(*args):
    new_dir = save_dir_var.get()
    if os.path.isdir(new_dir):
        save_config(new_dir)

save_dir_var.trace_add("write", on_save_dir_change)

path_frame = tk.Frame(save_frame)
path_frame.pack(fill=tk.X, pady=(5, 0))

path_entry = tk.Entry(path_frame, textvariable=save_dir_var, font=("Meiryo", 10))
path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)

change_dir_btn = tk.Button(path_frame, text="参照...", command=choose_directory, font=("Meiryo", 10), width=8)
change_dir_btn.pack(side=tk.RIGHT, padx=(10, 0))

# --- 手動リネームボックスエリア ---
rename_frame = tk.LabelFrame(root, text="📝 ファイル名おまかせ", font=("Meiryo", 10, "bold"), padx=10, pady=8)
rename_frame.pack(pady=8, fill=tk.X, padx=20)

tk.Label(rename_frame, text="手動", font=("Meiryo", 10)).grid(row=0, column=0, sticky=tk.W, padx=(0, 4))

manual_prefix_var = tk.StringVar()
prefix_entry = tk.Entry(rename_frame, textvariable=manual_prefix_var, font=("Meiryo", 11))
prefix_entry.grid(row=0, column=1, sticky=tk.EW, padx=(0, 8))

# 連番開始番号指定
tk.Label(rename_frame, text="開始", font=("Meiryo", 10)).grid(row=0, column=2, sticky=tk.E, padx=(0, 2))
counter_var = tk.IntVar(value=1)

def on_counter_change(*args):
    global manual_rename_counter
    try:
        manual_rename_counter = int(counter_var.get())
    except:
        pass

counter_spin = tk.Spinbox(rename_frame, from_=1, to=9999, textvariable=counter_var, width=5, font=("Meiryo", 10), command=on_counter_change)
counter_spin.grid(row=0, column=3, padx=(0, 4))
counter_var.trace_add("write", on_counter_change)

# --- モードボタン（3択ラジオ）---
btn_row = tk.Frame(rename_frame)
btn_row.grid(row=1, column=0, columnspan=4, pady=(8, 0), sticky=tk.EW)

btn_manual = tk.Button(btn_row, text="📝 手動",
                       command=lambda: set_rename_mode("manual"),
                       font=("Meiryo", 10, "bold"), width=10)
btn_manual.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

btn_ai = tk.Button(btn_row, text="🤖 AIリネーム",
                   command=lambda: set_rename_mode("ai"),
                   font=("Meiryo", 10, "bold"), width=10)
btn_ai.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

btn_off = tk.Button(btn_row, text="⏹ 両方OFF",
                    command=lambda: set_rename_mode("off"),
                    font=("Meiryo", 10, "bold"), width=10)
btn_off.pack(side=tk.LEFT, fill=tk.X, expand=True)

rename_frame.columnconfigure(1, weight=1)

# 起動時に保存済みのモードを引き継ぎ
set_rename_mode(rename_mode)

listener = mouse.Listener(on_click=on_mouse_event)
listener.start()

root.mainloop()
