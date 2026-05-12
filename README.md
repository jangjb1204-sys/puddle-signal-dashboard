# Puddle Signal Scanner

Puddle Signal Scanner는 상위 미국 주식과 ETF를 주기적으로 스캔해서 **Puddle** 및 **RSI & Puddle** 신호가 발생한 종목만 CSV로 저장하는 자동화 프로젝트입니다.

현재 Streamlit 화면은 다음 단계로 미뤄두고, 우선은 GitHub Actions에서 스캐너를 자동 실행하여 날짜별 결과 파일을 쌓는 구조로 운영합니다.

---

## 전체 흐름

```text
GitHub Actions 실행
        ↓
puddle_rsi_signal_scanner.py 실행
        ↓
상위 주식 / ETF 티커 목록 수집
        ↓
Yahoo Finance 가격 데이터 다운로드
        ↓
이동평균선, RSI, Puddle 조건 계산
        ↓
신호가 발생한 종목만 필터링
        ↓
signal_scans/signal_scan_YYYYMMDD.csv 저장
        ↓
GitHub repo에 자동 commit / push
```

---

## 자동 실행 방식

GitHub Actions workflow는 `.github/workflows/update-signals.yml`에 정의되어 있습니다.

현재 실행 방식은 다음과 같습니다.

```yaml
schedule:
  - cron: "*/30 * * * *"
```

즉 GitHub Actions 기준으로 **30분마다 자동 실행**됩니다.

수동 실행도 가능합니다.

```text
GitHub repo → Actions → Update signal scan → Run workflow
```

---

## 저장 위치

스캔 결과는 루트 폴더가 아니라 `signal_scans/` 폴더 아래에 저장됩니다.

예시:

```text
signal_scans/
  signal_scan_20260512.csv
  signal_scan_20260513.csv
  signal_scan_20260514.csv
```

같은 날짜에는 같은 파일을 계속 덮어씁니다.

예를 들어 2026년 5월 12일에는 30분마다 아래 파일이 갱신됩니다.

```text
signal_scans/signal_scan_20260512.csv
```

다음 날이 되면 새 날짜 파일이 생성됩니다.

```text
signal_scans/signal_scan_20260513.csv
```

이 방식은 루트 폴더를 깔끔하게 유지하면서도 날짜별 이력을 남기기 위한 구조입니다.

---

## 스캔 대상

기본 스캔 대상은 다음과 같습니다.

| 구분 | 기본 소스 | 기본 개수 |
|---|---|---:|
| Stock | Slickcharts S&P 500 | 상위 100개 |
| ETF | ETFdb market cap ranking | 상위 100개 |

기본값은 코드 실행 옵션에서 변경할 수 있습니다.

```bash
python puddle_rsi_signal_scanner.py --stock-limit 200 --etf-limit 200
```

또는 직접 만든 CSV 파일을 넣어서 스캔 대상을 지정할 수도 있습니다.

```bash
python puddle_rsi_signal_scanner.py \
  --stocks-csv stocks.csv \
  --etfs-csv etfs.csv
```

CSV 파일은 아래처럼 ticker 컬럼을 가지면 됩니다.

```csv
ticker
AAPL
MSFT
SPY
QQQ
```

---

## 사용하는 데이터

가격 데이터는 Yahoo Finance에서 가져옵니다.

기본 다운로드 기간은 2년입니다.

```bash
--period 2y
```

각 종목에 대해 주로 사용하는 가격 컬럼은 다음과 같습니다.

```text
Open
High
Low
Close
```

추가로 시장 참고 데이터도 함께 가져옵니다.

| 항목 | 티커 | 의미 |
|---|---|---|
| 10Y Treasury | `^TNX` | 미국 10년물 금리 |
| VIX | `^VIX` | 변동성 지수 |
| VIX1D | `^VIX1D` | 1일 변동성 지수 |
| SKEW | `^SKEW` | 꼬리위험 / 극단적 리스크 참고 지표 |

현재 최종 CSV에는 핵심 신호 결과만 저장하며, 위 시장 데이터는 내부 계산/확장용으로 사용됩니다.

---

## 계산하는 지표

각 종목별로 아래 지표를 계산합니다.

```text
Change(%)
MA20
MA60
MA120
MA200
RSI
Puddle
```

### Change(%)

전일 종가 대비 등락률입니다.

```text
Change(%) = 오늘 종가 / 전일 종가 - 1
```

CSV에는 `change_pct` 컬럼으로 저장됩니다.

### Moving Average

아래 이동평균선을 계산합니다.

```text
MA20
MA60
MA120
MA200
```

Puddle 단계 판단에 사용됩니다.

### RSI

기본 14일 RSI를 계산합니다.

```text
RSI window = 14
```

RSI가 30 이하이면 과매도 구간으로 판단합니다.

---

## Puddle 신호 로직

Puddle은 종가가 주요 이동평균선을 위에서 아래로 이탈할 때 발생합니다.

### 1st Puddle

```text
오늘 종가 < MA20
전일 종가 >= 전일 MA20
```

출력 문구:

```text
1st: MA20, 10% cash
```

### 2nd Puddle

```text
오늘 종가 < MA60
전일 종가 >= 전일 MA60
```

출력 문구:

```text
2nd: MA60, 50% cash, 5d
```

### 3rd Puddle

```text
오늘 종가 < MA120
전일 종가 >= 전일 MA120
```

출력 문구:

```text
3rd: MA120, 50% cash, 5d
```

### 4th Puddle

```text
오늘 종가 < MA200
전일 종가 >= 전일 MA200
RSI < 30
```

출력 문구:

```text
4th: MA200, RSI<=30, 100% cash, 40d
```

여러 Puddle 조건이 동시에 발생하면 가장 높은 단계가 선택됩니다.

우선순위는 다음과 같습니다.

```text
4th > 3rd > 2nd > 1st
```

---

## 최종 신호 구분

CSV에 저장되는 최종 신호는 두 종류입니다.

| signal | 의미 |
|---|---|
| Puddle | Puddle 조건이 발생한 종목 |
| RSI & Puddle | Puddle 조건 발생 + RSI 30 이하 |

즉 `RSI & Puddle`은 단순히 RSI만 낮은 종목이 아니라, **Puddle 신호가 발생했고 동시에 RSI도 30 이하인 종목**입니다.

---

## 출력 CSV에서 확인할 수 있는 것

출력 파일은 아래 경로에 생성됩니다.

```text
signal_scans/signal_scan_YYYYMMDD.csv
```

CSV 컬럼은 다음과 같습니다.

| 컬럼 | 설명 |
|---|---|
| `scan_timestamp_utc` | 스캐너가 실행된 UTC 기준 시각 |
| `date` | 실제 가격 데이터 기준 날짜 |
| `asset_type` | `Stock` 또는 `ETF` |
| `ticker` | 종목 티커 |
| `signal` | `Puddle` 또는 `RSI & Puddle` |
| `close` | 해당 날짜 종가 |
| `change_pct` | 전일 대비 등락률 |
| `rsi` | 14일 RSI |
| `puddle` | 발생한 Puddle 단계와 대응 문구 |

예시:

```csv
scan_timestamp_utc,date,asset_type,ticker,signal,close,change_pct,rsi,puddle
2026-05-12T18:30:00+00:00,2026-05-12,Stock,AAPL,Puddle,182.15,-1.42,41.23,"1st: MA20, 10% cash"
2026-05-12T18:30:00+00:00,2026-05-12,ETF,QQQ,RSI & Puddle,421.88,-2.71,29.84,"4th: MA200, RSI<=30, 100% cash, 40d"
```

출력 CSV에는 전체 스캔 대상 종목이 모두 들어가지 않습니다.

저장되는 종목은 아래 조건 중 하나를 만족한 경우만입니다.

```text
Puddle 발생
또는
RSI & Puddle 발생
```

즉 신호가 없는 종목은 CSV에 저장되지 않습니다.

---

## 캐시 구조

Yahoo Finance 요청 제한을 줄이기 위해 가격 데이터는 `.puddle_yf_cache/`에 캐시됩니다.

```text
.puddle_yf_cache/
```

이 캐시는 GitHub repo에 직접 커밋하지 않습니다.

GitHub Actions에서는 cache 기능을 통해 다음 실행에 재사용합니다.

목적은 다음과 같습니다.

```text
Yahoo rate limit 완화
스캔 속도 개선
반복 다운로드 최소화
```

---

## 로컬 실행

필요 패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

기본 실행:

```bash
python puddle_rsi_signal_scanner.py
```

특정 날짜 기준 실행:

```bash
python puddle_rsi_signal_scanner.py --date 2026-05-12
```

테스트용으로 적은 종목만 실행:

```bash
python puddle_rsi_signal_scanner.py --stock-limit 5 --etf-limit 5
```

출력 파일 경로 직접 지정:

```bash
python puddle_rsi_signal_scanner.py --output test_scan.csv
```

---

## 현재 주요 파일

| 파일 | 역할 |
|---|---|
| `puddle_rsi_signal_scanner.py` | 티커 수집, 가격 다운로드, 지표 계산, 신호 판정, CSV 저장 |
| `.github/workflows/update-signals.yml` | GitHub Actions 자동 실행 설정 |
| `requirements.txt` | Python 의존성 |
| `signal_scans/` | 날짜별 스캔 결과 CSV 저장 폴더 |
| `app.py` | 향후 Streamlit 화면용 파일. 현재 핵심 자동화 흐름에서는 필수 아님 |

---

## 현재 프로젝트 상태

현재 목표는 Streamlit 대시보드보다 먼저 **신뢰 가능한 자동 스캔 및 CSV 이력 저장 구조**를 만드는 것입니다.

현재 완성된 기능은 다음과 같습니다.

```text
30분마다 자동 실행
상위 주식/ETF 스캔
Puddle / RSI & Puddle 신호 탐지
날짜별 CSV 저장
GitHub repo 자동 커밋
Yahoo Finance 캐시 사용
```

이후 확장 후보는 다음과 같습니다.

```text
Streamlit 대시보드 리뉴얼
최근 신호 요약 카드
날짜별 신호 변화 분석
종목별 신호 히스토리
ETF / Stock 비교
Puddle 단계별 통계
DuckDB 또는 SQLite 저장 구조
알림 기능
```
