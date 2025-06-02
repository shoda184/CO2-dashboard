# test_co2_accurate.py
import hid
import time
from datetime import datetime

class CO2MiniReader:
    def __init__(self):
        self.device = None
        self.buffer = []  # データバッファ
    
    def connect(self):
        """CO2miniデバイスに接続"""
        try:
            self.device = hid.device()
            self.device.open(0x04d9, 0xa052)
            print("✅ CO2miniデバイスに接続しました")
            
            # デバイス情報表示
            print(f"製品名: {self.device.get_product_string()}")
            print(f"メーカー: {self.device.get_manufacturer_string()}")
            return True
        except Exception as e:
            print(f"❌ 接続エラー: {e}")
            return False
    
    def read_raw_data(self):
        """生データを読み取り（8バイト）"""
        try:
            if self.device:
                return self.device.read(8)
            return None
        except Exception as e:
            print(f"データ読み取りエラー: {e}")
            return None
    
    def parse_co2_message(self, raw_data):
        """CO2miniの5バイトメッセージを解析"""
        if not raw_data or len(raw_data) < 5:
            return None
        
        # 5バイトメッセージを抽出
        item_code = raw_data[0]
        msb = raw_data[1] 
        lsb = raw_data[2]
        checksum = raw_data[3]
        cr = raw_data[4]
        
        # 終端コード確認
        if cr != 0x0D:
            return {'error': f'無効な終端コード: {hex(cr)} (期待値: 0x0D)'}
        
        # チェックサム検証
        calculated_checksum = (item_code + msb + lsb) & 0xFF
        if checksum != calculated_checksum:
            return {
                'error': f'チェックサムエラー: {hex(checksum)} != {hex(calculated_checksum)}'
            }
        
        # データ値を計算
        value = (msb << 8) | lsb
        
        # Item コードによる分岐
        if item_code == 0x50:  # CO2濃度
            return {
                'type': 'CO2',
                'value': value,
                'unit': 'ppm',
                'raw': [hex(x) for x in raw_data[:5]],
                'valid': True
            }
        elif item_code == 0x42:  # 温度
            # 温度は100分の1℃単位だが、実際の値計算は仕様書要確認
            # 一般的には value / 100.0 または特別な計算式
            temperature = value / 100.0  # とりあえず100で割る
            return {
                'type': 'Temperature', 
                'value': temperature,
                'unit': '°C',
                'raw': [hex(x) for x in raw_data[:5]],
                'valid': True
            }
        else:
            return {
                'type': 'Unknown',
                'item_code': hex(item_code),
                'value': value,
                'raw': [hex(x) for x in raw_data[:5]],
                'valid': False
            }
    
    def read_and_parse(self):
        """データを読み取って解析"""
        raw_data = self.read_raw_data()
        if raw_data:
            return self.parse_co2_message(raw_data)
        return None
    
    def disconnect(self):
        """デバイス切断"""
        if self.device:
            self.device.close()
            self.device = None
            print("🔌 デバイス切断")

def test_co2_parsing():
    """CO2miniデータ解析テスト"""
    
    print("=== CO2mini正確データ解析テスト ===")
    print("仕様: 5バイトメッセージ (Item + MSB + LSB + Checksum + CR)")
    print("")
    
    reader = CO2MiniReader()
    
    if not reader.connect():
        return False
    
    print("\n📡 データ読み取り開始...")
    print("Item | MSB  | LSB  | Sum  | CR   | Type     | Value    | Status")
    print("-" * 70)
    
    co2_values = []
    temp_values = []
    error_count = 0
    
    try:
        for i in range(15):  # 15回読み取り
            result = reader.read_and_parse()
            
            if result:
                raw = result.get('raw', ['--'] * 5)
                status = "✅" if result.get('valid') else "❌"
                
                if result.get('error'):
                    print(f"{raw[0]:4s} | {raw[1]:4s} | {raw[2]:4s} | {raw[3]:4s} | {raw[4]:4s} | ERROR    | {result['error']:8s} | ❌")
                    error_count += 1
                elif result['type'] == 'CO2':
                    co2_values.append(result['value'])
                    print(f"{raw[0]:4s} | {raw[1]:4s} | {raw[2]:4s} | {raw[3]:4s} | {raw[4]:4s} | CO2      | {result['value']:4d} ppm | {status}")
                elif result['type'] == 'Temperature':
                    temp_values.append(result['value'])
                    print(f"{raw[0]:4s} | {raw[1]:4s} | {raw[2]:4s} | {raw[3]:4s} | {raw[4]:4s} | 温度     | {result['value']:6.1f}°C | {status}")
                else:
                    print(f"{raw[0]:4s} | {raw[1]:4s} | {raw[2]:4s} | {raw[3]:4s} | {raw[4]:4s} | 不明     | Code:{result.get('item_code', '??'):4s} | ❓")
            else:
                print("--   | --   | --   | --   | --   | NO DATA  | --------  | ⏸️")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ 停止しました")
    
    reader.disconnect()
    
    # 結果サマリー
    print("\n" + "=" * 70)
    print("📊 測定結果サマリー:")
    
    if co2_values:
        print(f"🌬️  CO2測定: {len(co2_values)}回")
        print(f"   最新値: {co2_values[-1]} ppm")
        print(f"   平均値: {sum(co2_values)/len(co2_values):.1f} ppm")
        print(f"   範囲: {min(co2_values)} - {max(co2_values)} ppm")
    else:
        print("🌬️  CO2測定: データなし")
    
    if temp_values:
        print(f"🌡️  温度測定: {len(temp_values)}回")
        print(f"   最新値: {temp_values[-1]:.1f} °C")
        print(f"   平均値: {sum(temp_values)/len(temp_values):.1f} °C")
        print(f"   範囲: {min(temp_values):.1f} - {max(temp_values):.1f} °C")
    else:
        print("🌡️  温度測定: データなし")
    
    if error_count > 0:
        print(f"⚠️  エラー: {error_count}回")
    
    success_rate = ((len(co2_values) + len(temp_values)) / 15) * 100
    print(f"📈 成功率: {success_rate:.1f}%")
    
    return len(co2_values) > 0 or len(temp_values) > 0

def test_continuous_monitoring():
    """連続モニタリングテスト"""
    
    print("\n=== 連続モニタリングテスト ===")
    print("リアルタイムでCO2と温度を表示します")
    print("Ctrl+Cで停止\n")
    
    reader = CO2MiniReader()
    
    if not reader.connect():
        return False
        
    latest_co2 = None
    latest_temp = None
    
    try:
        while True:
            result = reader.read_and_parse()
            current_time = datetime.now().strftime("%H:%M:%S")
            
            if result and result.get('valid'):
                if result['type'] == 'CO2':
                    latest_co2 = result['value']
                    print(f"[{current_time}] 🌬️  CO2: {latest_co2:4d} ppm", end="")
                    if latest_temp is not None:
                        print(f" | 🌡️  温度: {latest_temp:5.1f}°C")
                    else:
                        print()
                        
                elif result['type'] == 'Temperature':
                    latest_temp = result['value']
                    print(f"[{current_time}] 🌡️  温度: {latest_temp:5.1f}°C", end="")
                    if latest_co2 is not None:
                        print(f" | 🌬️  CO2: {latest_co2:4d} ppm")
                    else:
                        print()
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print(f"\n\n📋 最終測定値:")
        print(f"🌬️  CO2: {latest_co2 if latest_co2 else '--'} ppm")
        print(f"🌡️  温度: {latest_temp if latest_temp else '--'} °C")
    
    reader.disconnect()
    return True

if __name__ == "__main__":
    # 基本解析テスト
    success = test_co2_parsing()
    
    if success:
        response = input("\n連続モニタリングを開始しますか？ (y/n): ")
        if response.lower() == 'y':
            test_continuous_monitoring()
    else:
        print("\n❌ 基本テストでデータが取得できませんでした")
        print("デバイスの接続と設定を確認してください")
