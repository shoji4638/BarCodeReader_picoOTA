#https://kousaku-prog.com/ili9341msp2807/#toc3

#sample01.py
#ili9341.py
#xglcd_font.py
#fonts\Unispace12x24.c

from machine import Pin, UART, SPI
from xglcd_font import XglcdFont
from ili9341 import Display, color565
import utime
import network
import time
import socket
import sys

from ota import OTAUpdater
#from WIFI_CONFIG import SSID, PASSWORD

#firmware_url = "https://raw.githubusercontent.com/shoji4638/BarCodeReader_picoOTA/"
#firmware_url = "https://github.com

x_offset = 10
y_offset = 10

CONTROL_HOST = '10.16.1.41'
PORT = 12345
BUFSIZE = 4096
FORMAT = 'utf-8'

# ************** Read ssid_file *****************
def read_ssid_file(ssid_file):
    ssid_dic = {}
    with open(ssid_file, 'r') as file:
        while True:
            content = file.readline()
            if content == '':
 #               print("ファイルの終端に達しました。")
                break
            content = content.strip()
            content = content.split(',')
            ssid_dic[content[0].encode()] = content[1]
            
#    print(ssid_dic)
    return ssid_dic


def scan_best_wifi(_SSID_LIST,_display):
    try:
        print('\n****** Scan Best WiFi *********')
        wlan=network.WLAN(network.WLAN.IF_STA)
        wlan.active(True)
        scans = wlan.scan()
        best_ssid = [b'',b'',0,-100,0,0]
        n = 2

#        for n, SSID in enumerate(list(_SSID_LIST)):
        _display.draw_text(x_offset, y_offset+(n)*24, 'RSSI: SSID', font,color565(r, g, b))
        for SSID in list(_SSID_LIST):
#            print('SSID:',SSID)
            for scan in scans:
#                print(' ',scan[0],end="")
                if SSID == scan[0]:
                    _display.draw_text(x_offset, y_offset+(1+n)*24, f'{scan[3]} : {SSID.decode()}', font,color565(r, g, b))
                    n += 1
                    if best_ssid[3] < scan[3]:
                       best_ssid = scan
#                       print(scan)    #(ssid, bssid, channel, RSSI, security, hidden)

        wlan.disconnect()
#        print('Best_SSID:',best_ssid[0],' Pass:',_SSID_LIST[best_ssid[0]])
#        print('Best_SSID:',best_ssid[0],' Pass:',_SSID_LIST[best_ssid[0]])
        print('\nBest_SSID:',best_ssid[0].decode())
        
    except Exception as e:
        print(f'予期せぬエラーが発生しました: {e}')
#        led_error.on()
        sys.exit(1)
        wlan = None
    
    finally:
        return best_ssid


# ************** WiFi connect *****************
def wifi_connect(SSID,PW,_display):
    try:
        print(f'\n***** WiFi {SSID} connecting Try *****')
        #display.text('SSID:%s' % SSID[1], 0, 20, 1)
        _display.draw_text(x_offset, y_offset, f'SSID:{SSID}', font,color565(255, 0, 0))
#        _display.show()

        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
#        wlan.connect(SSID, PW)
        wlan.connect(SSID, PW)
        wait=0

        while wlan.isconnected() == False:
            #WiFi接続待ち
            led_wifi.off()
            wait+=1
            print(f'Connecting SSID {SSID} router {wait}')
            time.sleep_ms(800)
            led_wifi.on()
            #display.text(' @ ' , (wait%16)*8, 30, 1)
            _display.draw_text(10+(wait%16)*8, 64, ' * ', font,color565(255, 0, 0))
            #_display.show()
            time.sleep_ms(200)
        else:
            led_wifi.on()
            #display.fill(0) # 表示内容消去
            _display.clear()
            _display.draw_text(x_offset, y_offset, 'WiFi connected!', font,color565(0, 0, 255))
            #display.text('WiFi connected!', 0, 0, 1)
            #display.text(' SSID:%s' % SSID, 0, 10, 1)
            _display.draw_text(x_offset, y_offset+1*24, f'SSID:{SSID}', font,color565(0, 0, 255))
            wlan_status = wlan.ifconfig()

            #print(type(wlan_status[0]))  #str
            #display.text(' %s' %wlan_status[0], 0, 20, 1)
            _display.draw_text(x_offset, y_offset+2*24, f'IP:{wlan_status[0]}', font,color565(0, 0, 255))
            _display.draw_text(x_offset, y_offset+3*24, f'MASK:{wlan_status[1]}', font,color565(0, 0, 255))
            _display.draw_text(x_offset, y_offset+4*24, f'GW:{wlan_status[2]}', font,color565(0, 0, 255))
            _display.draw_text(x_offset, y_offset+5*24, f'DNS:{wlan_status[3]}', font,color565(0, 0, 255))
            #_display.show()

            print('\nWiFi Connected!')
            print(f' SSID:{SSID}')
            print(f' IP Address: {wlan_status[0]}')
            print(f' Netmask: {wlan_status[1]}')
            print(f' Default Gateway: {wlan_status[2]}')
            print(f' Name Server: {wlan_status[3]}')
            networks = wlan.scan()
            ssid_list = []
#            for scan in scans:
#                print(' ',scan[0],end="")
#                if SSID == scan[0]:

            for net in networks:
                if SSID.encode() == net[0]:
                    print(f' RSSI: {net[3]}')
            
            led_error.off()

    except Exception as e:
        print(f'to {SSID}に接続した際に予期せぬエラーが発生しました: {e}')
        led_error.on()
        sys.exit(1)
        wlan = None
    
    finally:
        return wlan
    
    
#************* シリアル割込み処理（BarCodeに入力アリ） **************
def show_received_message(uart):
    start = time.ticks_ms() # ミリ秒カウンター値を取得
    try:
        led_code.on()
        print('\n********* BarCoder Read **********')
        display.clear() # 表示内容消去    
        # 文字表示（"表示内容", x, y, 色）
#        display.text('BarCode Read', 0, 0, 1)
        display.draw_text(x_offset, y_offset, "BarCode Reader", font,color565(255, 255, 255))
        received_txt = uart.read()
#        display.text(received_txt[:13], 0, 10, 1)	#一般的なバーコード [:13]で最後の￥ｒ（リターン）を除く
#        display.text(received_txt[:-1], 0, 10, 1)	#最後の￥ｒ（リターン）を除く
        display.draw_text(x_offset, y_offset+1*24, received_txt[:-1], font,color565(255, 255, 255))
#        display.show()
#        time.sleep_ms(1000)
#    print('\nBarCodeData:',type(received_txt), received_txt)
        print(f'\n00:BarCodeData:{received_txt[:-1]} len:',len(received_txt),' type:',type(received_txt))
    except NoneType:
        print(f'バーコード読み込み時に「NoneType:」エラーが発生しました: {e}')
        clinet = None
        led_error.on()
        
    except Exception as e:
        print(f'バーコード読み込み時に予期せぬエラーが発生しました: {e}')
#        client.close()
        clinet = None
        led_error.on()
    else:
        led_code.off()

    try:    #01. Preparing Socket : socket()
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        led_db.on()
    except OSError as e:
        clinet = None
        print('\n********* socket ERROR ***********')
        print(f'{e}')
        led_error.on()
    else:
        print('01:socket OK')

    try:    #02. Configuring Soccket and Connect to the Server : connect()
        client.connect((CONTROL_HOST,PORT))
    except OSError as e:
        print('\n********* connect ERROR **********')
        print(f'to {CONTROL_HOST}.{PORT} connect ERROR: {e}')
        client.close()
        clinet = None
        led_error.on()
    except Exception as e:
        print('\n********* connect ERROR **********')
        print(f'to {CONTROL_HOST}.{PORT}に接続した際に予期せぬエラーが発生しました: {e}')
        client.close()
        clinet = None
        led_error.on()
    else:
        print('02:connect OK')
        led_db.off()
        
    if client is None:
        print('\n************ ERROR **************')
        print(f'Socket/connectでエラーが発生しました。終了します。')
        sys.exit(1)

    try:    #03. Data　Yaritori : send(), recv()
    # サーバーへのメッセージ
        client.sendall(received_txt)
        print(' Send  :',received_txt)
        # サーバーからのメッセージを受信
        data = client.recv(BUFSIZE)
        print(' Recive:',data.decode(FORMAT))
    except Exception as e:
        print('\n********* Write/Read ERROR **********')
        print(f'Write/Read中に予期せぬエラーが発生しました: {e}')
        client.close()
        clinet = None
        led_error.on()
    else:
        print('03:send/recive OK')
        #04. Closing the connection : close()
        client.close()
        delta = time.ticks_diff(time.ticks_ms(), start) # 時差を計算
#        display.text(f'SUCCESS!:{delta}ms', 0, 20, 1)	#一般的なバーコード
        display.draw_text(x_offset, y_offset+2*24, f'SUCCESS!:{delta}ms', font,color565(255, 255, 255))
        print(f'データベースへの記録に成功しました。処理時間: {delta}ms')


try:
    print('\n***INIT I/O SPI:LCD ILI9341 ***')
    led = Pin("LED", Pin.OUT, value=0)  # LEDピンをOFF状態で定義
    led_error = Pin(20, Pin.OUT, value=0)  # LEDピンをOFF状態で定義
    led_wifi = Pin(26, Pin.OUT, value=0)  # LEDピンをOFF状態で定義
    led_code = Pin(22, Pin.OUT, value=0)  # LEDピンをOFF状態で定義
    led_db = Pin(21, Pin.OUT, value=0)  # LEDピンをOFF状態で定義
    
    spiMSP     = SPI(0, baudrate=51200000, sck=Pin(6), mosi=Pin(7))
    display = Display(spiMSP, dc=Pin(15), cs=Pin(13), rst=Pin(14))
    #display = Display(spiMSP, dc=Pin(15), cs=Pin(13), rst=Pin(14), rotation=90)
    #display = Display(spiMSP, dc=Pin(15), cs=Pin(13), rst=Pin(14), rotation=90, width=320, height=240)
    font    = XglcdFont("fonts/Unispace12x24.c", 12, 24)
    r=255
    g=255
    b=255

    display.draw_text(x_offset, y_offset, "BarCode Reader", font,color565(r, g, b))
    display.draw_text(x_offset, y_offset+1*24, " WiFi Scan.....", font,color565(r, g, b))
#    display.draw_text(10, 64, " Ver 4", font,color565(r, g, b))
#    display.draw_text(10, 10, "Hello minasan", font,color565(200, 100, 25))
#    display.draw_circle(50, 90, 30, color565(0, 255, 223))
#    display.fill_rectangle(120, 100, 80, 50, color565(128, 200, 255))
#    display.draw_text8x8(40,40,"Hello world",color565(211,200,50))
#    def clup():
#        utime.sleep(100)
#        display.clear()
#    clup()

except Exception as e:
    print(f'起動初期化中に予期せぬエラーが発生しました: {e}')
    led_error.on()
    sys.exit(1)
    
#ota_updater = OTAUpdater(SSID, PASSWORD, firmware_url, "main.py")
#ota_updater.download_and_install_update_if_available()

try:
    print('\n*** OTA WiFi connect ***')
    led_wifi.on()
    ssids_dic = read_ssid_file('ssid_list.txt')
#    display.draw_text8x8(20, 70, "Read [ssid_list.txt]",color565(r, g, b))
    print('ssid_file:',ssids_dic)

    best_wifi_Status = scan_best_wifi(ssids_dic,display)
    SSID = best_wifi_Status[0].decode()
    PASSWORD = ssids_dic[best_wifi_Status[0]]
    display.clear()
    display.draw_text(0, y_offset+1*24, 'Best　WiFi　SSID', font,color565(r, g, b))
#    display.draw_text(10, 224, f'ID:{best_wifi_Status[0].decode()}', font,color565(r, g, b))
    display.draw_text(x_offset, y_offset+2*24, f'{SSID}', font,color565(r, g, b))
#    display.draw_text(10, 248, f'PW:{ssids_dic[best_wifi_Status[0]]}', font,color565(r, g, b))
    display.draw_text(0, y_offset+3*24, 'Password', font,color565(r, g, b))
    display.draw_text(x_offset, y_offset+4*24, f'PW:{PASSWORD}', font,color565(r, g, b))
#    print('Best SSID:',best_wifi_Status[0],' Pass:',ssids_dic[best_wifi_Status[0]])
    print('Best SSID:',SSID,' Pass:',PASSWORD)
    
    firmware_url = "https://raw.githubusercontent.com/shoji4638/BarCodeReader_picoOTA/"

#    ota_updater = OTAUpdater(SSID, PASSWORD, firmware_url, "main.py")
    ota_updater = OTAUpdater(SSID, PASSWORD, firmware_url, "main.py")
    display.draw_text(0, y_offset+5*24, f'On_Ver:{ota_updater.current_version}->OTA:', font,color565(r, g, b))
    ota_updater.download_and_install_update_if_available()
    if ota_updater.current_version == ota_updater.latest_version:
        display.draw_text(170, y_offset+5*24, f'{ota_updater.latest_version}', font,color565(0, 0, 255))
    else:
        display.draw_text(170, y_offset+5*24, f'{ota_updater.latest_version}', font,color565(255, 0, 0))
        
    uart = UART(0, 9600)  # 与えたボーレートで初期化
    #シリアル割込み設定
    uart.irq(handler=show_received_message, trigger=UART.IRQ_RXIDLE)

#    wlan = wifi_connect(best_wifi_Status[0].decode(),ssids_dic[best_wifi_Status[0]],display)
#    print('\nPlase read BarCode:')
except Exception as e:
    print(f'OTA確認中に予期せぬエラーが発生しました: {e}')
    led_error.on()
    sys.exit(1)

try:
    print('\n*** WiFi connect ***')
    led_wifi.on()
#    ssids_dic = read_ssid_file('ssid_list.txt')
#    print('ssid_file:',ssids_dic)

#    best_wifi_Status = scan_best_wifi(ssids_dic)
#    print('Best SSID:',best_wifi_Status[0],' Pass:',ssids_dic[best_wifi_Status[0]])
    #wlan = wifi_connect(SSID,PW)
#    wlan = wifi_connect(best_wifi_Status[0].decode(),ssids_dic[best_wifi_Status[0]])
    wlan = wifi_connect(SSID,PASSWORD,display)
    #send_data = 0
    print('\nPlase read BarCode:')
except Exception as e:
    print(f'OTA確認OK　WiFi接続中に予期せぬエラーが発生しました: {e}')
    led_error.on()
    sys.exit(1)


display.clear()

while True:
    try:
        if wlan.status() == 3: #WiFi接続中
#            print(wlan.status(),end='')
            networks = wlan.scan()
            ssid_list = []
#            for scan in scans:
#                print(' ',scan[0],end="")
#                if SSID == scan[0]:
            for net in networks:
                if SSID.encode() == net[0]:
                    display.draw_text(0, 11*24, f'{SSID}', font,color565(r, g, b))
                    if net[3] > -60:
                        display.draw_text(0, 12*24, f'RSSI: {net[3]} dBm', font,color565(0, 0, 255))
                    elif net[3] > -70:
                        display.draw_text(0, 12*24, f'RSSI: {net[3]} dBm', font,color565(255, 255, 0))
                    else:
                        display.draw_text(0, 12*24, f'RSSI: {net[3]} dBm', font,color565(255, 0, 0))
                    print(f'{SSID} RSSI: {net[3]}')
        else:
            print('\n******* WiFi connecting  ********')
            led_error.on()
            print('ReConnect WiFi')
            display.clear()
            display.draw_text(0, y_offset+1*24, 'Best　WiFi　SSID', font,color565(r, g, b))
#            display.text('BarCode Reader', 1, 1, 1)    # 文字表示（"表示内容", x, y, 色）
#            display.text('WiFi Reconnecing', 1, 11, 1)
#            display.text(' Now!!!!!!!!!', 1, 21, 1)
#            display.rect(0, 0, 127, 32, 1)    #四角
#            display.show()
            time.sleep_ms(5000)
            machine.reset()
##            wlan = wifi_connect(best_wifi_Status[0],ssids_dic[best_wifi_Status[0]])
##            wlan = wifi_connect(SSID_LIST)
##            ssids_dic = read_ssid_file('ssid_list.txt')
##            print('ssids_dic:',ssids_dic)

##            best_wifi_Status = scan_best_wifi(ssids_dic)
##            print('Best SSID:',best_wifi_Status)
##            print('Best SSID:',best_wifi_Status[0],' Pass:',ssids_dic[best_wifi_Status[0]])

    except Exception as e:
        led_error.on()
        print(f'wifi not connect/wlan.status() connect: {e}')

        time.sleep_ms(5000)

        machine.reset()

#        ssids_dic = read_ssid_file('ssid_list.txt')
#        print('ssids_dic:',ssids_dic)

#        best_wifi_Status = scan_best_wifi(ssids_dic)

#        print('Best SSID:',best_wifi_Status)
#        print('Best SSID:',best_wifi_Status[0],' Pass:',ssids_dic[best_wifi_Status[0]])

#        wlan = wifi_connect(SSID,PW)
        #wlan = wifi_connect(SSID,PW)
#        wlan = wifi_connect(ssids_dic)
        
#        if wlan.status() != 3:
#        print('Reconnect ! WiFi:',wlan.status())    
#        wlan = wifi_connect(SSID,PW)
#        sys.exit(1)
    else:
        time.sleep_ms(10000)

