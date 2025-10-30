from flask import Flask, Response, request, render_template_string
from flask_cors import CORS
import os, time, threading, requests

app = Flask(__name__)
CORS(app)

latest_frame = None
TD_URL = "http://127.0.0.1:9980"  # WebServer DAT 주소 (TouchDesigner용)

# 🔹 TouchDesigner가 매 프레임마다 보낸 이미지 저장
@app.route("/upload", methods=["POST"])
def upload():
    global latest_frame
    f = request.files["frame"]
    f.save("latest.jpg")
    latest_frame = "latest.jpg"
    return "ok"

# 🔹 실시간 스트리밍 (mjpeg)
def generate():
    last_sent = 0
    last_frame = None  # ✅ 이전 프레임 저장

    while True:
        try:
            if latest_frame and os.path.exists(latest_frame):
                with open(latest_frame, "rb") as f:
                    frame = f.read()
                last_frame = frame  # ✅ 최신 프레임 갱신
            elif last_frame:
                frame = last_frame  # ✅ 새 프레임 없으면 이전 프레임 유지
            else:
                time.sleep(0.05)
                continue

            # 약 20fps 출력
            if time.time() - last_sent > 0.05:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
                last_sent = time.time()
        except Exception as e:
            print("⚠️ Stream error:", e)
            time.sleep(0.1)



@app.route("/stream")
def stream():
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

# 🔹 버튼 클릭 시 TD에 신호 전달 (비동기)
def handle_shape_change(shape):
    print(f"✅ Received shape {shape}")
    try:
        requests.get(f"{TD_URL}/shape/{shape}", timeout=0.3)
    except Exception as e:
        print("❌ TD not connected:", e)

@app.route("/send", methods=["POST"])
def receive_shape():
    data = request.get_json()
    shape = data.get("shape")
    threading.Thread(target=handle_shape_change, args=(shape,)).start()
    return {"status": "ok"}

# 🔹 웹 페이지 구성
@app.route("/")
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
      <title>TouchDesigner Stream</title>
      <style>
        body { background:#fff; color:#fff; text-align:center; font-family:sans-serif; }
        button { margin:10px; padding:10px 20px; font-size:16px; cursor:pointer; }
        img { width:100vw; bmargin-top:20px; }
      </style>
    </head>
    <body>
      
      <div>
        <button onclick="sendShape(1)">Shape 1</button>
        <button onclick="sendShape(2)">Shape 2</button>
        <button onclick="sendShape(3)">Shape 3</button>
      </div>
      <img id="stream" src="/stream" alt="stream not available" style="max-width:90%;" onerror="this.src='/stream'">
      <script>
        const img = document.getElementById('stream');
        const originalSrc = img.src;

        function sendShape(num){
          fetch('/send', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({shape:num})
          })
          .then(r=>r.json())
          .then(d=>{
            console.log('sent shape', num);
            // 🔹 이미지 리로드를 막기 위해 src 다시 설정하지 않음
            // 🔹 스트림 깨졌을 때만 복구하도록 처리
            if (img.src !== originalSrc) img.src = originalSrc;
          })
          .catch(err=>{
            console.error(err);
          });
        }

        // 🔹 TouchDesigner 스트림이 끊겨도 자동 복구
        img.addEventListener('error', ()=>{
          console.log('stream error, reconnecting...');
          setTimeout(()=>{ img.src = originalSrc + '?t=' + Date.now(); }, 500);
        });
      </script>
    </body>
    </html>
    """)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, threaded=True)
