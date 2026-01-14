#https://kousaku-prog.com/ili9341msp2807/#toc3

#sample01.py
#ili9341.py
#xglcd_font.py
#fonts\Unispace12x24.c

from machine import Pin, SPI
from xglcd_font import XglcdFont
from ili9341 import Display, color565
import utime
import network
import time
import socket
import sys

from ota import OTAUpdater
from WIFI_CONFIG import SSID, PASSWORD

firmware_url = "https://github.com/shoji4638/BarCodeReader_picoOTA/main"


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
        n = 1

#        for n, SSID in enumerate(list(_SSID_LIST)):
        _display.draw_text(10, 90, 'RSSI: SSID', font,color565(r, g, b))
        for SSID in list(_SSID_LIST):
#            print('SSID:',SSID)
            for scan in scans:
#                print(' ',scan[0],end="")
                if SSID == scan[0]:
                    _display.draw_text(10, 92+n*24, f'{scan[3]} : {SSID.decode()}', font,color565(r, g, b))
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
        _display.draw_text(10, 40, f'SSID:{SSID}', font,color565(255, 0, 0))
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
            _display.draw_text(10, 10, 'WiFi connected!', font,color565(0, 0, 255))
            #display.text('WiFi connected!', 0, 0, 1)
            #display.text(' SSID:%s' % SSID, 0, 10, 1)
            _display.draw_text(10, 34, f'SSID:{SSID}', font,color565(0, 0, 255))
            wlan_status = wlan.ifconfig()

            #print(type(wlan_status[0]))  #str
            #display.text(' %s' %wlan_status[0], 0, 20, 1)
            _display.draw_text(10, 58, f'IP:{wlan_status[0]}', font,color565(0, 0, 255))
            _display.draw_text(10, 82, f'MASK:{wlan_status[1]}', font,color565(0, 0, 255))
            _display.draw_text(10,106, f'GW:{wlan_status[2]}', font,color565(0, 0, 255))
            _display.draw_text(10,130, f'DNS:{wlan_status[3]}', font,color565(0, 0, 255))
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

    display.draw_text(10, 10, "BarCode Reader", font,color565(r, g, b))
    display.draw_text(10, 40, " WiFi Scan.....", font,color565(r, g, b))
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
    
ota_updater = OTAUpdater(SSID, PASSWORD, firmware_url, "test.py")
ota_updater.download_and_install_update_if_available()


#try:
#    print('\n*** INIT WiFi connect ***')
#    led_wifi.on()
#    ssids_dic = read_ssid_file('ssid_list.txt')
##    display.draw_text8x8(5, 70, "Read[ssid_list.txt]", font,color565(r, g, b))
#    display.draw_text8x8(20, 70, "Read [ssid_list.txt]",color565(r, g, b))
#    print('ssid_file:',ssids_dic)
#
#    best_wifi_Status = scan_best_wifi(ssids_dic,display)
#    display.draw_text(10, 200, 'Best:', font,color565(r, g, b))
#    display.draw_text(10, 224, f'ID:{best_wifi_Status[0].decode()}', font,color565(r, g, b))
#    display.draw_text(10, 248, f'PW:{ssids_dic[best_wifi_Status[0]]}', font,color565(r, g, b))
#    print('Best SSID:',best_wifi_Status[0],' Pass:',ssids_dic[best_wifi_Status[0]])

#    wlan = wifi_connect(best_wifi_Status[0].decode(),ssids_dic[best_wifi_Status[0]],display)
#    print('\nPlase read BarCode:')
#except Exception as e:
#    print(f'起動初期化中に予期せぬエラーが発生しました: {e}')
#    led_error.on()
#    sys.exit(1)
