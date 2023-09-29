import os
from dotenv import load_dotenv
import interpreter
import json
import signal
import time
import sys

import subprocess
import pkg_resources

required_packages = ["python-dotenv", "open-interpreter"]

installed_packages = {pkg.key for pkg in pkg_resources.working_set}

for package in required_packages:
    if package not in installed_packages:
        subprocess.check_call(["pip", "install", package])

selected_key = None

def load_api_keys():
    load_dotenv()
    api_keys = os.getenv("OPENAI_API_KEYS")
    
    if not api_keys:
        new_key = input("OpenAI APIキーが見つかりませんでした。新しいキーを入力してください：")
        with open(".env", "a") as f:
            f.write(f"\nOPENAI_API_KEYS={new_key}")
        os.environ["OPENAI_API_KEY"] = new_key
        return [new_key]
    else:
        os.environ["OPENAI_API_KEY"] = api_keys.split(',')[0]
        return api_keys.split(',')

def load_system_message():
    # .envをロード
    load_dotenv()
    # INTERPRETER_SYSTEM_MESSAGEを取得、デフォルトは空文字列
    return os.getenv("INTERPRETER_SYSTEM_MESSAGE", "")

def save_system_message(message):
    # .envにシステムメッセージを保存
    with open('.env', 'a') as f:
        f.write(f"\nINTERPRETER_SYSTEM_MESSAGE={message}")
    
def save_chatlog(messages):
    with open("chatlog.json", "w") as f:
        json.dump(messages, f)

def load_chatlog():
    try:
        with open("chatlog.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def select_api_key(api_keys):
    while True:
        print("\n選択可能なAPIキー：")
        for idx, key in enumerate(api_keys):
            print(f"{idx + 1}. {key}")
        print(f"{len(api_keys) + 1}. キーを追加")
        print(f"{len(api_keys) + 2}. キーを削除")
        print(f"{len(api_keys) + 3}. キーを編集")
        print(f"{len(api_keys) + 4}. 終了")
        
        choice = int(input("選択してください："))
        
        if 1 <= choice <= len(api_keys):
            return api_keys[choice - 1]
        elif choice == len(api_keys) + 1:
            new_key = input("新しいキーを入力してください：")
            api_keys.append(new_key)
            with open(".env", "a") as f:
                f.write(f",{new_key}")
        elif choice == len(api_keys) + 2:
            del_choice = int(input("削除するキーの番号を選択してください："))
            del api_keys[del_choice - 1]
            with open(".env", "w") as f:
                f.write(f"OPENAI_API_KEYS={','.join(api_keys)}")
        elif choice == len(api_keys) + 3:
            edit_choice = int(input("編集するキーの番号を選択してください："))
            new_key = input("新しいキーを入力してください：")
            api_keys[edit_choice - 1] = new_key
            with open(".env", "w") as f:
                f.write(f"OPENAI_API_KEYS={','.join(api_keys)}")
        elif choice == len(api_keys) + 4:
            break

def main():
    messages = []
    global selected_key

    # APIキーのロードと選択
    api_keys = load_api_keys()
    if len(api_keys) > 1:
        selected_key = select_api_key(api_keys)
    else:
        selected_key = api_keys[0]

    # 以前の会話のロード
    previous_messages = load_chatlog()
    if previous_messages:
        interpreter.load(previous_messages)

    def signal_handler(sig, frame):
        print("\nプログラムが中断されました。会話を保存します。")
        save_chatlog(messages)
        sys.exit(0)

    # signalモジュールを使用して、Ctrl+Cが押されたときにsignal_handler関数を呼び出すように設定
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        print("\n--- メニュー ---")
        print("1. 新しい会話をはじめる")
        print("2. 以前の会話を復元する")
        print("3. システムメッセージの変更")
        print("4. ローカルモデルの実行（※オプション）")
        print("5. 終了")
        choice = int(input("選択してください："))

        if choice == 1:
            messages = interpreter.chat()
        elif choice == 2:
            previous_messages = load_chatlog()
            if previous_messages:
                interpreter.load(previous_messages)
                messages = interpreter.chat()
            else:
                print("以前の会話はありません。")
                messages = interpreter.chat()
        elif choice == 3:
            current_message = interpreter.system_message
            print(f"現在のシステムメッセージ：\n{current_message}")
            new_message = input("新しいシステムメッセージを追加してください：")
            interpreter.system_message += new_message
            save_system_message(new_message)
        elif choice == 4:
            print("必要に応じて各自で実装してください。")
            time.sleep(3)
        elif choice == 5:
            break

if __name__ == "__main__":
    main()
