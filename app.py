from flask import Flask, Response, request, render_template
from flask_cors import CORS
import os, time, threading, requests

app = Flask(__name__)
CORS(app)

latest_frame = None
TD_URL = "http://127.0.0.1:9980"

@app.route("/upload", methods=["POST"])
def upload():
    global latest_frame
    f = request.files["frame"]
    f.save("latest.jpg")
    latest_frame = "latest.jpg"
    return "ok"

def generate():
    last_sent = 0
    while True:
        if latest_frame and os.path.exists(latest_frame):
            if time.time() - last_sent > 0.05:
                with open(latest_frame, "rb") as f:
                    frame = f.read()
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                last_sent = time.time()
        else:
            time.sleep(0.05)

@app.route("/stream")
def stream():
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

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

@app.route("/")
def index():
    return render_template("index.html")   # ← HTML 파일 불러오기

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, threaded=True)
