import co2meter as co2
import datetime
import time # 時間を制御するためのライブラリ

def get_realtime_co2_data(interval_seconds=5):
    """
    CO2モニターからリアルタイムでデータを取得し、表示します。

    Args:
        interval_seconds (int): データを取得する間隔（秒）。デフォルトは5秒。
    """
    print("CO2モニターを初期化しています...")
    try:
        mon = co2.CO2monitor()
        print("CO2モニターの初期化に成功しました。")
    except Exception as e:
        print(f"CO2モニターの初期化に失敗しました: {e}")
        print("CO2モニターが正しく接続されているか、またはライブラリが正しくインストールされているか確認してください。")
        return # 初期化に失敗したら処理を終了

    print(f"\nリアルタイムデータ取得を開始します。Ctrl+Cで停止します。")
    print(f"取得間隔: {interval_seconds}秒")
    print("-" * 50)

    try:
        while True: # 永遠に繰り返すループ
            data = mon.read_data()
            timestamp, co2_value, temperature = data

            # 取得したデータを表示
            print(f"日時: {timestamp.strftime('%Y/%m/%d %H:%M:%S')}") # 見やすい形式に変換
            print(f"CO2濃度: {co2_value} ppm")
            print(f"温度: {temperature:.2f} °C")
            print("-" * 50)

            time.sleep(interval_seconds) # 指定された秒数だけ待機する
            
    except KeyboardInterrupt:
        # Ctrl+Cが押されたらループを終了
        print("\nデータ取得を停止しました。")
    except Exception as e:
        print(f"\nデータ取得中にエラーが発生しました: {e}")

if __name__ == "__main__":
    # データを5秒ごとに取得します
    get_realtime_co2_data(interval_seconds=5)
