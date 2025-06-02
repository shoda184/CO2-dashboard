import co2meter as co2
import datetime
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading

# Flaskアプリケーションの初期化
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Flask-SocketIOの初期化
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# CO2モニターの初期化
co2_monitor = None
try:
    co2_monitor = co2.CO2monitor()
    print("CO2モニターの初期化に成功しました。")
except Exception as e:
    print(f"CO2モニターの初期化に失敗しました: {e}")
    print("CO2モニターが正しく接続されているか確認してください。")
    co2_monitor = None

# データ取得用のスレッド
def background_thread():
    """
    CO2モニターからデータを定期的に読み込み、接続されている全てのクライアントに送信する。
    """
    if co2_monitor is None:
        print("CO2モニターが利用できないため、テストデータを送信します。")
        # テスト用のダミーデータを送信
        send_test_data()
        return

    print("データ取得スレッドを開始しました。")
    interval_seconds = 5

    while True:
        try:
            data = co2_monitor.read_data()
            timestamp, co2_value, temperature = data

            current_data = {
                'timestamp': timestamp.strftime('%Y/%m/%d %H:%M:%S'),
                'co2': co2_value,
                'temp': f"{temperature:.2f}"
            }

            socketio.emit('new_co2_data', current_data)
            print(f"データ送信: {current_data}")

        except Exception as e:
            print(f"データ取得中にエラーが発生しました: {e}")
            current_data = {
                'timestamp': datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                'co2': 'エラー',
                'temp': 'エラー'
            }
            socketio.emit('new_co2_data', current_data)
        
        time.sleep(interval_seconds)

def send_test_data():
    """
    CO2モニターが利用できない場合のテストデータ送信
    """
    import random
    interval_seconds = 5
    base_co2 = 400
    base_temp = 22.0
    
    print("テストデータの送信を開始します。")
    
    while True:
        try:
            # ランダムなテストデータを生成
            co2_value = base_co2 + random.randint(-50, 100)
            temp_value = base_temp + random.uniform(-2.0, 3.0)
            
            current_data = {
                'timestamp': datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                'co2': co2_value,
                'temp': f"{temp_value:.2f}"
            }

            socketio.emit('new_co2_data', current_data)
            print(f"テストデータ送信: {current_data}")
            
        except Exception as e:
            print(f"テストデータ送信中にエラーが発生しました: {e}")
        
        time.sleep(interval_seconds)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def test_connect():
    print('クライアントが接続しました。')
    # 接続時に歓迎メッセージを送信（オプション）
    emit('server_message', {'message': 'CO2モニターに接続しました'})

@socketio.on('disconnect')
def test_disconnect():
    print('クライアントが切断しました。')

if __name__ == '__main__':
    # データ取得スレッドを開始
    thread = threading.Thread(target=background_thread, daemon=True)
    thread.start()
    
    print("Webサーバーを起動しています...")
    print("ブラウザで http://localhost:5000 にアクセスしてください")
    
    # Webサーバーを起動
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
