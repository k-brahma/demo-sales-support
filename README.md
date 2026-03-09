# Python Sales Support デモアプリ集

営業支援の現場で説明しやすい題材に寄せた Tkinter デスクトップアプリ 10 本です。

各アプリは `main.py` に分析ロジック、`gui.py` に Tkinter UI を分離しています。

## 環境セットアップ

```powershell
uv venv .venv-linux --python 3.14
uv pip install --python .venv-linux/bin/python -r requirements.txt
```

## 起動方法

```powershell
cd 01_lead_scoring_workbench
../.venv-linux/bin/python gui.py
```

## アプリ一覧

### 01 見込み顧客スコアリング
![01 見込み顧客スコアリング](img/sales_01_lead_scoring_workbench.png)

### 02 フォロータイミング最適化
![02 フォロータイミング最適化](img/sales_02_followup_timing_optimizer.png)

### 03 商談停滞検知
![03 商談停滞検知](img/sales_03_pipeline_stall_detector.png)

### 04 見積粗利チェッカー
![04 見積粗利チェッカー](img/sales_04_quote_margin_checker.png)

### 05 営業活動量トラッカー
![05 営業活動量トラッカー](img/sales_05_sales_activity_tracker.png)

### 06 顧客離反シグナル監視
![06 顧客離反シグナル監視](img/sales_06_customer_churn_signal_monitor.png)

### 07 キャンペーン反応分析
![07 キャンペーン反応分析](img/sales_07_campaign_response_analyzer.png)

### 08 売上見込みシミュレーター
![08 売上見込みシミュレーター](img/sales_08_sales_forecast_simulator.png)

### 09 アカウント深耕マップ
![09 アカウント深耕マップ](img/sales_09_account_penetration_map.png)

### 10 訪問優先順位ボード
![10 訪問優先順位ボード](img/sales_10_visit_plan_builder.png)

