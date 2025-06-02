import co2meter as co2
import datetime
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading

# Flaskアプリケーションの初期化
app = Flask(__name__)
# Flask-SocketIOの初期化 (WebSocket通信用)
app.config['SECRET_KEY'] = 'your_secret_key_here' # 本番環境ではもっと複雑なキーにしてください
socketio = SocketIO(app)

# CO2モニターの初期化 (グローバルに設定して、どこからでもアクセスできるようにする)
# サーバー起動時に一度だけ初期化する
co2_monitor = None
try:
    co2_monitor = co2.CO2monitor()
    print("CO2モニターの初期化に成功しました。")
except Exception as e:
    print(f"CO2モニターの初期化に失敗しました: {e}")
    print("CO2モニターが正しく接続されているか確認してください。")
    # 初期化に失敗してもサーバーは起動させるが、データは取得できないことを示す
    co2_monitor = None

# データ取得用のスレッド（メインのWebサーバーとは別に動く）
def background_thread():
    """
    CO2モニターからデータを定期的に読み込み、接続されている全てのクライアントに送信する。
    """
    if co2_monitor is None:
        print("CO2モニターが利用できないため、データ取得スレッドは開始されません。")
        return

    print("データ取得スレッドを開始しました。")
    # データを取得する間隔（秒）
    interval_seconds = 5

    while True:
        try:
            data = co2_monitor.read_data()
            timestamp, co2_value, temperature = data

            # 取得したデータを辞書形式にまとめる
            # JavaScriptで扱いやすいようにタイムスタンプを文字列に変換
            current_data = {
                'timestamp': timestamp.strftime('%Y/%m/%d %H:%M:%S'),
                'co2': co2_value,
                'temp': f"{temperature:.2f}" # 小数点以下2桁にフォーマット
            }

            # 接続されている全てのWebブラウザにデータを送信
            # 'new_co2_data'という名前のイベントでデータを送信
            socketio.emit('new_co2_data', current_data)
            print(f"データ送信: {current_data}")

        except Exception as e:
            print(f"データ取得中にエラーが発生しました: {e}")
            current_data = {
                'timestamp': datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                'co2': 'エラー',
                'temp': 'エラー'
            }
            socketio.emit('new_co2_data', current_data) # エラー時も通知
        
        time.sleep(interval_seconds)

# Webページのルート（ホームページ）
@app.route('/')
def index():
    """
    クライアントがWebサーバーにアクセスしたときに表示するHTMLファイルを返す。
    """
    return render_template('index.html')

# クライアントがWebSocketに接続したときの処理
@socketio.on('connect')
def test_connect():
    print('クライアントが接続しました。')
    # 接続時に初期データ（もしあれば）を送信することも可能

# クライアントがWebSocketから切断したときの処理
@socketio.on('disconnect')
def test_disconnect():
    print('クライアントが切断しました。')

# アプリケーション起動時の処理
if __name__ == '__main__':
    # データ取得スレッドをWebサーバーとは別に起動
    # daemon=True にすると、メインプログラムが終了したらスレッドも自動で終了する
    thread = threading.Thread(target=background_thread, daemon=True)
    thread.start()

    # Webサーバーを起動
    # host='0.0.0.0' にすると、Raspberry PiのIPアドレスで外部からアクセスできるようになる
    # port=5000 はデフォルトのポート番号
    socketio.run(app, host='0.0.0.0', port=5000, debug=False) # debug=True は開発時のみ
