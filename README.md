# binance · TradingView 信号 → 币安合约自动下单

把 TradingView 的策略警报接成币安永续合约的真实下单：TradingView 发出 webhook →
ngrok 隧道 → 本地 Flask 收单 → 调用币安 API 开/平仓，可指定杠杆。

> 前身是同一个项目的早期版本，与 [USDT](../USDT) 共用同一套逻辑，这里保留最精简的一份。

## 数据流

```
TradingView 警报
      │  POST JSON
      ▼
  ngrok 公网 URL
      │
      ▼
 Flask :5000  ──▶  binance.client  ──▶  币安永续合约
```

## 文件

| 文件 | 作用 |
|---|---|
| `main.py` | Flask webhook 接收端 + 下单逻辑（限价开仓、市价平仓） |
| `text.py` | 本地测试用，往 webhook 发一条假信号 |
| `requirements.txt` | 依赖 |

## 配置

```bash
cp .env.example .env
```

`.env` 里填三项：`BINANCE_API_KEY`、`BINANCE_API_SECRET`、`NGROK_URL`。
代码用 `os.getenv` 读取，**仓库里不含任何密钥**。

## 运行

```bash
pip install -r requirements.txt
python main.py            # 起 Flask
ngrok http 5000           # 另开一个终端
```

把 ngrok 给的 `https://xxx.ngrok-free.app` 填进 `.env` 的 `NGROK_URL`，再把同一个地址粘到 TradingView 警报的 Webhook URL。

## 警报格式

```json
{
  "order": "1",
  "symbol": "ARBUSDT",
  "signal": "{{strategy.order.comment}}",
  "price": "{{close}}",
  "leverage": "50"
}
```

- `order`：`1` 开仓，`0` 关闭交易
- `signal`：`Buy` 开多 / `Sell` 开空 / `tlong` 平多 / `tshort` 平空

策略里的 `strategy.order.comment` 必须输出这四个词之一。

## 注意

- 开仓默认挂在市价 0.1% 处限价，平仓走市价
- 币安 API 需要开「允许合约交易」权限，建议绑定 IP 白名单
- 先用小额或测试网跑通再上实盘
