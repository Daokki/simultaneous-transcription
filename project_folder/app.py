# app.py
from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import threading
import queue
import time
from googletrans import Translator

app = Flask(__name__)

# 音声認識と翻訳のキュー
transcription_queue = queue.Queue()
translation_queue = queue.Queue()

# 音声認識の継続フラグ
is_listening = False

def recognize_speech():
    """バックグラウンドで音声認識を実行する関数"""
    global is_listening
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        # ノイズ調整
        recognizer.adjust_for_ambient_noise(source)
        
        while is_listening:
            try:
                print("音声を聞いています...")
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                
                # 音声をテキストに変換（英語）
                english_text = recognizer.recognize_google(audio, language="en-US")
                
                if english_text:
                    print(f"認識された英語: {english_text}")
                    # キューに追加
                    transcription_queue.put(english_text)
                    
                    # 翻訳
                    translator = Translator()
                    japanese_text = translator.translate(english_text, src='en', dest='ja').text
                    translation_queue.put(japanese_text)
                    
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                print("音声を認識できませんでした")
                continue
            except Exception as e:
                print(f"エラーが発生しました: {e}")
                continue
                
    print("音声認識を停止しました")

@app.route('/')
def index():
    """メインページを表示"""
    return render_template('index.html')

@app.route('/start_listening', methods=['POST'])
def start_listening():
    """音声認識の開始"""
    global is_listening
    
    if not is_listening:
        is_listening = True
        # 別スレッドで音声認識を開始
        threading.Thread(target=recognize_speech).start()
        return jsonify({"status": "started"})
    
    return jsonify({"status": "already_running"})

@app.route('/stop_listening', methods=['POST'])
def stop_listening():
    """音声認識の停止"""
    global is_listening
    
    if is_listening:
        is_listening = False
        return jsonify({"status": "stopped"})
    
    return jsonify({"status": "not_running"})

@app.route('/get_transcription', methods=['GET'])
def get_transcription():
    """最新の文字起こしを取得"""
    transcriptions = []
    translations = []
    
    # キューから全ての文字起こしを取得
    while not transcription_queue.empty():
        transcriptions.append(transcription_queue.get())
        
    # キューから全ての翻訳を取得
    while not translation_queue.empty():
        translations.append(translation_queue.get())
        
    return jsonify({
        "transcriptions": transcriptions,
        "translations": translations
    })

if __name__ == "__main__":
    app.run(debug=True)