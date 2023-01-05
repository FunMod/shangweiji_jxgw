import PySimpleGUI as sg
import time
from serial import Serial
import threading
import serial.tools.list_ports

ser = None
receive = ''
port_list = list(serial.tools.list_ports.comports())
baud_rate = ('115200', '9600', '4800', '1200', '210')
my_dict = {"复位控制器": "A5", "读取温度": "50", "读取加速度": "51", "读取电流": "52", 
           "读取模拟量1": "55", "读取模拟量2": "56", "读取模拟量3": "57", "读取RTD": "58", 
           "读取42V模拟": "59", "推挽1 ON": "5A", "推挽1 OFF": "5B", "推挽2 ON": "5C", 
           "推挽2 OFF": "5D", "推挽3 ON": "5F", "推挽3 OFF": "60", "GPIO1 ON": "61", 
           "GPIO1 OFF": "62", "GPIO2 ON": "63", "GPIO2 OFF": "64", "UART 发送X": "65", 
           "UART 读取": "66", "读取井下控制器心跳信号": "67", "读取井下控制器开机秒数": "68", }
key_list = my_dict.keys()
print(list(key_list))
context = "等待接收数据中..."
temp_context = " "
CMD_NOW = ""


def find_ports():
    global port_list
    port_list = list(serial.tools.list_ports.comports())
    # print(port_list)
    if len(port_list) == 0:
        print('无可用串口')
    else:
        for i in range(0, len(port_list)):
            print(port_list[i])


def con_serial(com, bps, timeout):
    global ser
    global receive
    try:
        # 端口，GNU / Linux上的/ dev / ttyUSB0 等 或 Windows上的 COM3 等
        portx = com
        # 波特率，标准值之一：50,75,110,134,150,200,300,600,1200,1800,2400,4800,9600,19200,38400,57600,115200
        bps = bps
        # 超时设置,None：永远等待操作，0为立即返回请求结果，其他值为等待超时时间(单位为秒）
        timex = timeout
        # 打开串口，并得到串口对象
        ser = Serial(portx, bps, timeout=timex, bytesize=8, parity='N', stopbits=1)
        # print("串口详情参数：", ser)
        # ser.close()#关闭串口
    except Exception as e:
        print("---异常---", e)
        return False


def send_data(text):
    global ser
    result = ser.write(text)    # 写数据
    ser.flush()
    print("写总字节数:", result)


def long_function_thread(window):
    global ser
    global receive
    global context
    global CMD_NOW
    while True:
        try:
            n = ser.inWaiting()
            if n:
                time.sleep(0.1)
                n = ser.inWaiting()
                print('读取数量：'+str(n))
                rec_byte = ser.read(n)
                print(hex(rec_byte[0])[2:])
                print(CMD_NOW)
                if rec_byte[0] == 0xA1:
                    # print("接收井下数据超时！")
                    context = "来自井下数据超时！"
                    window['-STATUS_CON-'].update(context)
                elif (rec_byte[0] == 0x61) and (hex(rec_byte[0])[2:] == CMD_NOW):
                    context = "成功！"
                    window['-STATUS_CON-'].update(context)
                elif (rec_byte[0] == 0x62) and (hex(rec_byte[0])[2:] == CMD_NOW):
                    context = "成功！"
                    window['-STATUS_CON-'].update(context)
                else:
                    context = "不是合法数据！"
                    window['-STATUS_CON-'].update(context)
                for i in bytearray(rec_byte):
                    receive = receive + hex(i) + " "
                receive = receive + "\r\n"
        except Exception as e:
            print("---异常---", e)
            print('接收发生错误')
            break
    window.write_event_value('-THREAD DONE-', '')


def long_function():
    threading.Thread(target=long_function_thread, args=(window,), daemon=True).start()


menu_def = [['File', ['Exit']], 
            ['Help', 'About...'], ]
tab1_layout = [[sg.Text(text="请连接设备后选择指令！", key="-STATUS-"), sg.Text(text=' ', key="-STATUS_CON-")],
                [sg.Push(), sg.Multiline(size=(50, 10), key='-RECV-', autoscroll=True), sg.Push()]]
tab2_layout = [[sg.Text(text='状态监控')],
            [sg.Push(), sg.Output(size=(50, 10)), sg.Push()],
            [sg.Push()]]
sg.theme('Light Gray 1')
layout = [[sg.Menu(menu_def, )], 
          [sg.Push(), sg.Frame(layout=[
            [sg.Button(button_text='扫描设备', key="-SCAN-"),  sg.Push(), sg.Text(text='选择设备:'),sg.Combo(port_list, default_value=port_list[0], size=(20, len(port_list)), key='-PORTS-')],
            [sg.Button(button_text='连接设备', key="-CON-"), sg.Text(text='状态:未连接', key="-CONSTATE-"), sg.Push(), sg.Text(text='波特率:'), sg.InputCombo(baud_rate, size=(15, 1), default_value="9600", key="-RATE-")]], title='连接设备', size=(390, 100)), sg.Push()],
          [sg.Push(), sg.Frame(layout=[
            [sg.Text(text='当前指令')],
            [sg.Input(key='-CMD-', size=(50, 20))],
            [sg.Button(button_text="发送指令", key="-SEND-"), sg.Push(), sg.Button(button_text="清空记录", key='-CLS-')],
            [sg.Listbox(list(key_list), size=(50, len(list(key_list))), key='-CMDLIST-')]], title='发送指令', size=(390, 300)), sg.Push()],
          [sg.Push(), sg.TabGroup([[sg.Tab('数据记录', tab1_layout, tooltip='数据记录'), sg.Tab('Debug', tab2_layout)]], tooltip='Debug窗口'), sg.Push()],
          ]

window = sg.Window('高温井下控制系统(Demo)', layout)

while True:  # Event Loop
    event, values = window.read(timeout=100)
    # print(event, values)
    if event in (sg.WIN_CLOSED, 'Exit'):
        try:
            ser.close()
            break
        except Exception as e:
            print("---异常---", e)
            break
    if event == '-SCAN-':
        find_ports()
        window['-PORTS-'].update(values=port_list)
    if event == "-CON-":
        print(str(values["-PORTS-"]).split(" ", 1)[0])
        print(str(values["-RATE-"]))
        if con_serial(str(values["-PORTS-"]).split(" ", 1)[0], str(values["-RATE-"]), 5) is False:
            sg.popup("连接失败")
            ser = None
        else:
            sg.popup("连接成功"+str(values["-PORTS-"]).split(" ", 1)[0])
            window['-CONSTATE-'].update("状态:已连接")
            print('开始接收数据：')
            long_function()
    if event == '-THREAD DONE-':
        window['-CONSTATE-'].update("状态:未连接")
        sg.popup("串口连接断开")
        print('串口连接断开')
    if values['-CMDLIST-']:
        # print(my_dict[values['-CMDLIST-'][0]])
        if (temp_context != values['-CMDLIST-'][0]) and (ser is not None):
            CMD_NOW = str(my_dict[values['-CMDLIST-'][0]])
            window['-CMD-'].update(str(my_dict[values['-CMDLIST-'][0]]))
            window['-STATUS-'].update(str(values['-CMDLIST-'][0])+": ")
            context = "等待接收数据中..."
            window['-STATUS_CON-'].update(context)
            temp_context = values['-CMDLIST-'][0]
    if event == "-SEND-":
        try:
            if ser is not None:
                print(values["-CMD-"])
                send_data(bytes.fromhex(values["-CMD-"]))
            else:
                sg.popup("请先连接串口！")
        except Exception as e:
            print("---异常---", e)
            sg.popup("发送错误")
    if event == "-CLS-":
        receive = ''

    window['-RECV-'].update(receive)

window.close()
