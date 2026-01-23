from machine import Pin, UART, SPI
from xglcd_font import XglcdFont
from ili9341 import Display, color565
import utime
import network
import time
import socket
import sys
from ota import OTAUpdater

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
                break
            content = content.strip()
            content = content.split(',')
            ssid_dic[content[0].encode()] = content[1]
            
    return ssid_dic


def scan_best_wifi(_SSID_LIST,_display):
    try:
        print('\n****** Scan Best WiFi *********')
        wlan=network.WLAN(network.WLAN.IF_STA)
        wlan.active(True)
        scans = wlan.scan()
        best_ssid = [b'',b'',0,-100,0,0]
        n = 2

        _display.draw_text(x_offset, y_offset+(n)*24, 'RSSI: SSID', font,color565(r, g, b))
        for SSID in list(_SSID_LIST):
            for scan in scans:
                if SSID == scan[0]:
                    _display.draw_text(x_offset, y_offset+(1+n)*24, f'{scan[3]} : {SSID.decode()}', font,color565(r, g, b))
                    n += 1
                    if best_ssid[3] < scan[3]:
                       best_ssid = scan

        wlan.disconnect()
        print('\nBest_SSID:',best_ssid[0].decode())
        
    except Exception as e:
        print(f'予期せぬエラーが発生しました: {e}')
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

            _display.draw_text(x_offset, y_offset+2*24, f'IP:{wlan_status[0]}', font,color565(0, 0, 255))
            _display.draw_text(x_offset, y_offset+3*24, f'MASK:{wlan_status[1]}', font,color565(0, 0, 255))
            _display.draw_text(x_offset, y_offset+4*24, f'GW:{wlan_status[2]}', font,color565(0, 0, 255))
            _display.draw_text(x_offset, y_offset+5*24, f'DNS:{wlan_status[3]}', font,color565(0, 0, 255))

            print('\nWiFi Connected!')
            print(f' SSID:{SSID}')
            print(f' IP Address: {wlan_status[0]}')
            print(f' Netmask: {wlan_status[1]}')
            print(f' Default Gateway: {wlan_status[2]}')
            print(f' Name Server: {wlan_status[3]}')
            networks = wlan.scan()
            ssid_list = []
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
        print('\n00:********* BarCoder Read **********')
        display.clear() # 表示内容消去    
        # 文字表示（"表示内容", x, y, 色）
#        display.text('BarCode Read', 0, 0, 1)
        display.draw_text(x_offset, y_offset, "BarCode Reader", font,color565(255, 255, 255))
        received_txt = uart.read()
        if type(received_txt) == bytes:
            print(f' Code:{received_txt} Type:Bytes')
            received_str = received_txt[:-1].decode('utf-8')
            print(f' Code:{received_str} len:{len(received_str)} Type:str')
            display.draw_text(x_offset, y_offset+1*24, received_str, font,color565(255, 255, 255))
            if int(received_str)>0:
                display.draw_text(x_offset+20*10, y_offset+1*24, 'OK', font,color565(0, 0, 255))
            else:
                display.draw_text(x_offset+20*10, y_offset+1*24, 'NG', font,color565(255, 0, 0))
        
    except Exception as e:
        print(f'バーコード読み込み時に予期せぬエラーが発生しました: {e}')
#        client.close()
        clinet = None
        led_error.on()
    else:
        led_code.off()
#        time.sleep(1)

    try:    #01. Preparing Socket : socket()
        led_db.on()
        print('01:******* socket connect... *********')
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except OSError as e:
        clinet = None
        print('\n !!!!!!! connecting ERROR !!!!!!')
        print(f'{e}')
        led_error.on()
        display.draw_text(x_offset, y_offset+2*24, ' Socket NG', font,color565(255, 0, 0))
    else:
        display.draw_text(x_offset, y_offset+2*24, ' Socket OK', font,color565(0, 0, 255))
        print(' socket OK')

    try:    #02. Configuring Soccket and Connect to the Server : connect()
        print('02:******* to server connecting ********')
        client.connect((CONTROL_HOST,PORT))
    except OSError as e:
        print('\n!!!!!!! connect ERROR (OSError) !!!!!!')
        print(f' to {CONTROL_HOST}.{PORT} connect ERROR: {e}')
        client.close()
        clinet = None
        led_error.on()
        display.draw_text(x_offset, y_offset+3*24, ' Connect NG', font,color565(255, 0, 0))
        print(f'Socket/connectでエラーが発生しました。終了します。')
        sys.exit(1)
    except Exception as e:
        print('\n!!!!!!! connect ERROR (Other) !!!!!!')
        print(f' to {CONTROL_HOST}.{PORT}に接続した際に予期せぬエラーが発生しました: {e}')
        client.close()
        clinet = None
        led_error.on()
        display.draw_text(x_offset, y_offset+3*24, ' Connect NG', font,color565(255, 0, 0))
        print(f'Socket/connectでエラーが発生しました。終了します。')
        sys.exit(1)
    else:
        print(f' kadoma_control_PC to {CONTROL_HOST}.{PORT} connect OK')
        led_db.off()
        
    try:    #03. Data　Yaritori : send(), recv()
    # サーバーへのメッセージ
        print('03:******* SEND to server ********')
        print(' Send  :',received_str+'_3')
        client.sendall(received_str+'_3')
        # サーバーからのメッセージを受信
        print(' Waiting Recive:',end='')
        data = client.recv(BUFSIZE)
        print(data.decode(FORMAT))
    except Exception as e:
        print('\n!!!!!!! Write/Read ERROR !!!!!!!')
        print(f'Write/Read中に予期せぬエラーが発生しました: {e}')
        client.close()
        clinet = None
        led_error.on()
        print(f'Socket/connectでエラーが発生しました。終了します。')
        sys.exit(1)
    else:
        print(' send/recive OK')
        #04. Closing the connection : close()
        client.close()
        delta = time.ticks_diff(time.ticks_ms(), start) # 時差を計算
#        display.text(f'SUCCESS!:{delta}ms', 0, 20, 1)	#一般的なバーコード
        display.draw_text(x_offset, y_offset+2*24, f'SUCCESS!:{delta}ms', font,color565(255, 255, 255))
        print(f'データベースへの記録に成功しました。処理時間: {delta}ms')


#************************* Main ***************************   
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

except Exception as e:
    print(f'起動初期化中に予期せぬエラーが発生しました: {e}')
    led_error.on()
    sys.exit(1)
    
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
    display.draw_text(x_offset, y_offset+2*24, f'{SSID}', font,color565(r, g, b))
    display.draw_text(0, y_offset+3*24, 'Password', font,color565(r, g, b))
#    print('Best SSID:',best_wifi_Status[0],' Pass:',ssids_dic[best_wifi_Status[0]])
    print('Best SSID:',SSID,' Pass:',PASSWORD)
    
    firmware_url = "https://raw.githubusercontent.com/shoji4638/BarCodeReader_picoOTA/"

    ota_updater = OTAUpdater(SSID, PASSWORD, firmware_url, "main.py")
    display.draw_text(0, y_offset+5*24, f'On_Ver:{ota_updater.current_version}->OTA:', font,color565(r, g, b))
    ota_updater.download_and_install_update_if_available()
    if ota_updater.current_version == ota_updater.latest_version:
        display.draw_text(170, y_offset+5*24, f'{ota_updater.latest_version}', font,color565(0, 0, 255))
    else:
        display.draw_text(170, y_offset+5*24, f'{ota_updater.latest_version}', font,color565(255, 0, 0))
        
except Exception as e:
    print(f'OTA確認中に予期せぬエラーが発生しました: {e}')
    led_error.on()
    sys.exit(1)

#*************** WiFi connect/Serial Start *********************
try:
    print('\n*** WiFi connect ***')
    led_wifi.on()
    wlan = wifi_connect(SSID,PASSWORD,display)

    display.clear()
    display.draw_text(0, y_offset+1*24, 'Serial BarCodeReader', font,color565(r, g, b))
    display.draw_text(0, y_offset+2*24, '  Init....', font,color565(r, g, b))

#    uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))	#OK
    uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))	#OK
    uart0.irq(handler=show_received_message, trigger=UART.IRQ_RXIDLE)
    display.draw_text(0, y_offset+2*24, ' Start IRQ StandBy', font,color565(r, g, b))
    display.draw_text(0, y_offset+3*24, ' Ready to read', font,color565(0, 0, 255))

    #send_data = 0
    
    print('\nPlase read BarCode:')
except Exception as e:
    print(f'OTA確認OK　WiFi接続中に予期せぬエラーが発生しました: {e}')
    led_error.on()
    sys.exit(1)



while True:
    try:
        if wlan.status() == 3: #WiFi接続中
#            print(wlan.status(),end='')
            networks = wlan.scan()
            ssid_list = []
            for net in networks:
                if SSID.encode() == net[0]:
                    display.draw_text(0, 11*24, f'{SSID}', font,color565(r, g, b))
                    if net[3] > -50:
                        display.draw_text(0, 12*24, f'RSSI: {net[3]} dBm', font,color565(0, 255, 0))
                    elif net[3] > -60:
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
#            display.rect(0, 0, 127, 32, 1)    #四角
            time.sleep_ms(5000)
            machine.reset()

    except Exception as e:
        led_error.on()
        print(f'wifi not connect/wlan.status() connect: {e}')

        time.sleep_ms(5000)

        machine.reset()

    else:
        time.sleep_ms(10000)

