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
    load_dotenv()
    return os.getenv("INTERPRETER_SYSTEM_MESSAGE", "")

def save_system_message(message):
    with open('.env', 'a') as f:
        f.write(f"\nINTERPRETER_SYSTEM_MESSAGE={message}")

def read_messages_json():
    messages_file_path = "messages.json"
    if os.path.exists(messages_file_path):
        with open(messages_file_path, "r") as f:
            messages = json.load(f)
    else:
        messages = []
    return messages

def save_messages_json(messages):
    messages_json = json.dumps(messages, indent=4, ensure_ascii=False)
    with open("messages.json", "w", encoding="utf-8") as f:
        f.write(messages_json)

def load_last_message():
    return read_messages_json()

def main():
    chat_messages = []
    global selected_key

    api_keys = load_api_keys()
    if len(api_keys) > 1:
        selected_key = select_api_key(api_keys)
    else:
        selected_key = api_keys[0]

    def signal_handler(sig, frame):
        print("\nプログラムが中断されました。会話を保存します。")
        save_messages_json(chat_messages)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    while True:
        print("\n--- メニュー ---")
        print("1. 新しい会話をはじめる")
        print("2. 処理実行時の確認を省略する")
        print("3. 以前の会話を復元する(※実装中)")
        print("4. システムメッセージの変更")
        print("5. ローカルモデルの実行（※オプション）")
        print("6. 終了")
        choice = int(input("選択してください："))

        if choice == 1:
            readline.parse_and_bind("tab: complete")
            while True:
                user_input = input("User：")
                if user_input == '!wq':
                    save_messages_json(chat_messages)
                    break
                messages = interpreter.chat(user_input)
                chat_messages.extend(messages)

        if choice == 2:
            print("確認なしにコマンドを実行させるモードです")
            # コード実行時の確認を省略するためのコマンドを設定
            interpreter_command = "interpreter --yes"
            
            readline.parse_and_bind("tab: complete")
            while True:
                user_input = input("User：")
                if user_input == '!wq':
                    save_messages_json(chat_messages)
                    break
                # interpreter_command を使用してコードを実行
                messages = subprocess.check_output(interpreter_command, input=user_input, text=True)
                chat_messages.extend(messages)

        elif choice == 3:
            print("いま実装中です、「１」の処理を行います")
            readline.parse_and_bind("tab: complete")
            while True:
                user_input = input("User：")
                if user_input == '!wq':
                    save_messages_json(chat_messages)
                    break
                messages = interpreter.chat(user_input)
                chat_messages.extend(messages)


            # 以下は実装途中です（すみません）
            '''
            last_messages = load_last_message()
            if last_messages:
                interpreter.reset()
                interpreter.load(last_messages)
                while True:
                    user_input = input("User：")
                    if user_input == '!wq':
                        print("Saving messages...") 
                        save_messages_json(chat_messages)
                        break
                    messages = interpreter.chat(user_input)
                    chat_messages.extend(messages)
            else:
                print("以前の会話はありません。")
            '''

        elif choice == 4:
            current_message = interpreter.system_message
            print(f"現在のシステムメッセージ：\n{current_message}")
            new_message = input("新しいシステムメッセージを追加してください：")
            interpreter.system_message += new_message
            save_system_message(new_message)

        elif choice == 5:
            print("必要に応じて各自で実装してください。")
            time.sleep(3)

        elif choice == 6:
            break

if __name__ == "__main__":
    main()
