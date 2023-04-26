#  Python处理Tradingview信号 
##  项目简介 （需要帮助可联系，Q 752465849，V ELEVEN-1100）
    本次项目利用Python flask框架，获取Tradingview获取发出的信号，进行交易处理。
    将本地ip转换为公网url软件为ngrok,自行百度使用方法。
    本次对象是——币安永续合约，可自选交易币对，杠杆倍数。
    交易完成后公众号推送通知（暂时失效）

    交易方式：收到信号，进行开平仓。
        默认为：市场价的0.1%位置限价开仓（提高利润，降低损失、手续费），市场价格平仓。


##  设置信息
-   添加库
  
        pip install -r requirements.text
-   修改代码
  
        添加币安api
        ngrok获取到的公网url。

-   在ngrok中获取到的公网url填入 Tradingview 警报Webhook。（需要会员）
    警报格式为：

        {
        "order":"1",#0为关闭交易
        "symbol": "ARBUSDT",#ETHUSDT，都是合约，不要加.p
        "signal": "{{strategy.order.comment}}",#Buy,Sell,tlong,tshort，这是要修改你的pine代码
        "price" : "{{close}}","leverage": "50"#不要超过上限
        }

-   测试警报是否生效
    运行text.py文件,检查是否成功输出账户信息，格式如下：

        {"availableBalance":0.0,"positions":{},"totalCrossUnPnl":0.0,"totalMarginBalance":0.0,"totalWalletBalance":0.0}
 ##   修改你的策略Pine代码交易信号：
        开多仓：Buy
        开空仓：Sell
        平多仓：tlong
        平空仓：tshort
