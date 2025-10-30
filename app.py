from flask import Flask, Response, request, render_template
from flask_cors import CORS
import os, time, threading, requests

app = Flask(__name__, template_folder='templates')
CORS(app)

latest_frame = None
last_good_frame = None
TD_URL = "http://127.0.0.1:9980"

@app.route("/upload", methods=["POST"])
def upload():
    global latest_frame
    f = request.files["frame"]
    f.save("latest.jpg")
    latest_frame = "latest.jpg"
    return "ok"

def generate():
    global last_good_frame
    while True:
        if latest_frame and os.path.exists(latest_frame):
            try:
                with open(latest_frame, "rb") as f:
                    frame = f.read()
                if len(frame) > 1000:  # 너무 작은 파일은 무시
                    last_good_frame = frame
                if last_good_frame:
                    yield (
                        b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                        + last_good_frame + b"\r\n"
                    )
            except Exception as e:
                print("⚠️ frame read error:", e)
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
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, threaded=True)
