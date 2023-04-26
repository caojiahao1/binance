from flask import Flask, request, jsonify
from binance.client import Client
import requests

token = 'token' # 公众号PushPlus推送加 获取token。暂时失效，连接VPN推送不了
api_key = 'api_key'#币安pai
api_secret = 'api_secret'
ngrok_url = "ngrok_url"# 这里将你 ngrok 创建的公网地址粘贴到下面的字符串中
client = Client(api_key, api_secret)

def send_notification(title, content,token):
    # PushPlus服务平台的API接口地址
    url = 'https://www.pushplus.plus/send'
    # 您在PushPlus网站上注册的token
    data = {
        'token': token,
        'title': title,
        'content': str(content)
    }
    # 向PushPlus发送POST请求以推送通知
    res = requests.post(url, data)
def get_account_info():
    account = client.futures_account()     #账户
    account_info = {
        'totalWalletBalance': float(account['totalWalletBalance']),
        'totalMarginBalance': float(account['totalMarginBalance']),
        'totalCrossUnPnl':float(account['totalCrossUnPnl']),
        'availableBalance':float(account['availableBalance']),
        'positions': {}
    }
    for position in account['positions']:
        if float(position['positionAmt']) != 0:
            asset = position['symbol'][:-len('USDT')]
            unrealizedProfit=float(position['unrealizedProfit'])
            marginBalance=float(position['positionInitialMargin'])
            roe = float(unrealizedProfit / marginBalance * 100)
            account_info['positions'][asset+'USDT'] = {
                'symbol': position['symbol'],
                'positionSide': position['positionSide'],
                'positionAmt' : position['positionAmt'],
                'entryPrice': float(position['entryPrice']),
                'unrealizedProfit': float(position['unrealizedProfit']),
                'roe': f'{round(roe, 4):.2f}%'
            }
    return account_info
def open_position(symbol, signal, leverage):

    # 获取交易对信息
    exchange_info = client.futures_exchange_info()
    for symbol_info in exchange_info['symbols']:
        if symbol_info['symbol'] == symbol:
            #pricePrecision = symbol_info['pricePrecision'] #获取价格精度
            quantity_precision = symbol_info['quantityPrecision']  # 获取数量精度
            break
            
    if leverage!=50:
        leverage11 = client.futures_change_leverage(symbol=symbol, leverage=leverage)
        print("杠杆修改成功！,当前杠杆倍数为：%s"%leverage)

    # 计算可用余额
    availableBalance = client.futures_account()["availableBalance"]
    available_balance = float(availableBalance) * leverage

    # 获取市场价格
    symbol_ticker = client.futures_symbol_ticker(symbol=symbol)
    price = float(symbol_ticker['price'])

    if signal == 'Buy':
        side = 'BUY'
        position_side = 'LONG'
        limit = round(price*(1-0.1/100),4)
        print('限价做多：%s'% limit)
    elif signal == 'Sell':
        side = 'SELL'
        position_side = 'SHORT'
        limit = round(price*(1+0.1/100),4)
        print('限价做空:%s'% limit)

    # 计算下单数量
    quantity = (available_balance * 0.95) / limit
    quantity = round(quantity, quantity_precision)

    # 下单
    order = client.futures_create_order(
        symbol=symbol,
        side=side,
        type='LIMIT',
        timeInForce='GTC',
        price =limit,
        quantity=quantity,
        positionSide=position_side,
        newOrderRespType='RESULT'
    )
    return order
def close_position(symbol):
    # 获取市场价格
    symbol_ticker = client.futures_symbol_ticker(symbol=symbol)
    price = float(symbol_ticker['price'])
    print("平仓价格为:%s"%price)

    # 获取当前仓位信息
    positions = get_account_info()["positions"]
    for i in positions:
        if i == symbol and positions[i]['positionAmt'] != 0:
            #print(positions[i])
            quantity = abs(float(positions[i]['positionAmt']))
            # 平仓
            if positions[i]['positionSide'] == 'LONG':
                side='SELL'
                positionSide='LONG'
            elif positions[i]['positionSide'] == 'SHORT':
                side='BUY'
                positionSide='SHORT'
            order = client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=quantity,
                    positionSide=positionSide,
                    newOrderRespType='RESULT'
                )
            return order
        # 没有持仓或者持仓数量为0，返回False
        return False
def execute_trade_signals(signal, symbol, leverage):
    # 查询并取消上次限价单
    noorder = client.futures_get_open_orders()
    for order in noorder:
        if order['status'] == 'NEW':
            client.futures_cancel_order(symbol=order['symbol'], orderId=order['orderId'])
            print("存在限价订单，取消上次限价成功")

    # 查询所有持仓
    account_info = client.futures_account()
    positions = account_info['positions']
    direction = 0  # 0 表示没有持仓，1 表示持有多头，-1 表示持有空头
    for position in positions:
        if position['symbol'] == symbol and float(position['positionAmt']) != 0:
            if position['positionSide'] == 'LONG':
                direction = 1
            elif position['positionSide'] == 'SHORT':
                direction = -1
            break

    orders = []
    #平仓操作
    if signal == 'tlong'  and direction ==1 :
        response = close_position(symbol=symbol)
        if 'orderId' in response:
            orders.append(response)
            print("当前存在多头，平多仓")

    elif signal == 'tshort' and direction ==-1 :
        response = close_position(symbol=symbol)
        if 'orderId' in response:
            orders.append(response)
            print("当前存在空头，平空仓")

    # 执行开仓操作
    if signal == 'Buy' and direction !=1 :#买入多头信号且不持有多仓
        if direction == -1:
            response = close_position(symbol=symbol)
            if 'orderId' in response:
                orders.append(response)
                print("当前存在空头，平空仓")
        response = open_position(symbol=symbol, signal=signal, leverage=leverage)
        if response.get('orderId'):
            orders.append(response)
            print("开多仓")
    elif signal == 'Sell' and direction != -1 :
        if direction == 1:
            response = close_position(symbol)
            if 'orderId' in response:
                orders.append(response)
                print("当前存在多头，平多仓")
        response = open_position(symbol=symbol, signal=signal, leverage=leverage)
        if response.get('orderId'):
            orders.append(response)
            print("开空仓")
    return orders
def data_processing(data,token=token):
    symbol = data['symbol']
    signal = data['signal']
    #price = data['price']
    leverage = int(data['leverage'])
    
    if data['order'] == '1':
        orders = execute_trade_signals(signal, symbol, leverage)
        if any('orderId' in order for order in orders):
            title = "订单已创建"
            print("订单已创建")
        else:
            print("订单未被创建")
            #send_notification('下单失败', data,token="token")
    elif data['order'] == '0':
        print("未确认下单")

    noorder = client.futures_get_open_orders()
    for order in noorder:
        if order['type'] == 'LIMIT':
            list={
                'symbol':order['symbol'],
                'price':order['price'],
                'positionSide':order['positionSide']
            }
            print("当前存在限价单：%s" % list)
    return 'ok'

#收到POST
app = Flask(__name__)
@app.route('/', methods=['POST'])
def receive_webhook():
    data = request.json
    print(data)
    # 在此处添加处理TradingView Webhook数据的代码
    data_processing(data)
    account_info = get_account_info()
    print("账户信息：%s" % account_info)

    return jsonify(account_info)
if __name__ == '__main__':
    ngrok_url = ngrok_url
    app.run(host='0.0.0.0', port=80)
