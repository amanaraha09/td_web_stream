# TD Web Stream (TouchDesigner ↔ Flask)

- `/` : 웹 페이지 (버튼 + 스트림)
- `/upload` : TD가 JPG 프레임 업로드
- `/stream` : MJPEG 스트림
- `/send` : 버튼 → TD에 shape 신호 전달

## 로컬 실행
```bash
pip install -r requirements.txt
python app.py
