"""用 Gemini TTS 為 index.html 裡的每個泰文單字產生發音，輸出 audio/ 資料夾和 audio.js。
用法：
  pip install -U google-genai
  export GEMINI_API_KEY="你的金鑰"      (Windows PowerShell：$env:GEMINI_API_KEY="你的金鑰")
  python generate_audio.py
已產生的檔案會被跳過，中途失敗可以重跑。
"""
import base64, json, os, re, time
from google import genai

MODEL = "gemini-3.8-flash-tts"   # 泰語目前只有這個模型支援（flash-lite 不支援）
VOICE = "Kore"                    # 可換成文件列出的其他聲音
STYLE = "clear and slightly slow, for a language learner"

client = genai.Client()           # 自動讀取環境變數 GEMINI_API_KEY
html = open("index.html", encoding="utf-8").read()
words = json.loads(re.search(r"const D=(\[\[.*?\]\]);", html, re.S).group(1))
os.makedirs("audio", exist_ok=True)

def synth(text):
    for attempt in range(4):      # 文件說偶爾會隨機 500，所以要重試
        try:
            r = client.interactions.create(
                model=MODEL,
                input=[{"type": "user_input", "content": [{
                    "type": "text", "text": text,
                    "annotations": [{"type": "speech_metadata", "style": STYLE}]}]}],
                response_format={"type": "audio"},
                generation_config={"speech_config": [{"voice": VOICE}]},
            )
            return base64.b64decode(r.output_audio.data)
        except Exception as e:
            print("  重試", attempt + 1, e)
            time.sleep(3 * (attempt + 1))
    raise SystemExit(f"「{text}」產生失敗，請稍後重跑")

table = {}
for i, w in enumerate(words):
    path = f"audio/{i:03d}.wav"
    if not os.path.exists(path):
        print(f"[{i + 1}/{len(words)}] {w[0]}  {w[2]}")
        open(path, "wb").write(synth(w[0]))
    table[w[0]] = "data:audio/wav;base64," + base64.b64encode(open(path, "rb").read()).decode()

open("audio.js", "w", encoding="utf-8").write("window.AUDIO=" + json.dumps(table, ensure_ascii=False) + ";")
print("完成：audio.js 大小", round(os.path.getsize("audio.js") / 1e6, 1), "MB")
