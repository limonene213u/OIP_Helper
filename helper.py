import os
from dotenv import load_dotenv
import interpreter
import json
import signal
import time
import sys
# OS判別
if os.name == 'posix':  # UNIX系の場合
    import readline
elif os.name == 'nt':  # Windowsの場合
    import pyreadline as readline

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

def read_messages_json():
    """
    Read messages history from temp directory
    :return: list of messages
    """
    messages_file_path = "messages.json"
    if os.path.exists(messages_file_path):
        with open(messages_file_path, "r") as f:
            messages = json.load(f)
    else:
        messages = []
    return messages

def save_messages_json(messages):
    """
    Save messages history to temp directory
    :param messages: list of messages
    """
    messages_json = json.dumps(messages, indent=4, ensure_ascii=False)
    with open("messages.json", "w", encoding="utf-8") as f:
        f.write(messages_json)

def load_last_message():
    chatlog = read_messages_json()
    if chatlog:
        return [chatlog[-1]]  # 最後のメッセージだけをリストとして返す
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
    chat_messages = []
    global selected_key

    # APIキーのロードと選択
    api_keys = load_api_keys()
    if len(api_keys) > 1:
        selected_key = select_api_key(api_keys)
    else:
        selected_key = api_keys[0]

    def signal_handler(sig, frame):
        print("\nプログラムが中断されました。会話を保存します。")
        save_chatlog(chat_messages)
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
            readline.parse_and_bind("tab: complete")
            while True:
                user_input = input("User：")
                if user_input == ':!q':
                    messages = interpreter.chat('%save_message')  # 対話内容を保存
                    break
                messages = interpreter.chat(user_input)

        elif choice == 2:
            last_messages = load_last_message()
            if last_messages:
                messages = interpreter.chat("My name is limonene.", return_messages=True)
                interpreter.reset()
                interpreter.load(messages)
                while True:
                    user_input = input("User：")
                    if user_input == ':!q':
                        save_messages_json(messages)  # 対話内容を保存
                        break
                    messages = interpreter.chat(user_input)
            else:
                print("以前の会話はありません。")
                break

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
