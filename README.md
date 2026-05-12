# Puddle Signal Scanner

Puddle Signal Scanner는 미국 대형주와 대표 ETF를 자동으로 훑어보고, **Puddle** 또는 **RSI & Puddle** 신호가 발생한 종목만 CSV로 저장하는 자동 스캐너입니다.

이 프로젝트의 현재 목적은 화면이 예쁜 대시보드를 만드는 것이 아니라, 먼저 **GitHub Actions가 알아서 주기적으로 스캔하고, 날짜별 CSV 결과를 안정적으로 남기는 것**입니다.

---

## 아주 간단히 말하면

이 프로젝트는 아래 일을 자동으로 합니다.

```text
미국 대형주 / 대표 ETF 목록 준비
        ↓
Yahoo Finance에서 가격 데이터 다운로드
        ↓
이동평균선과 RSI 계산
        ↓
Puddle 신호가 발생한 종목만 골라냄
        ↓
signal_scans 폴더에 날짜별 CSV 저장
        ↓
GitHub에 자동 커밋
```

신호가 없는 종목은 CSV에 저장하지 않습니다. 그래서 결과 파일은 전체 종목 목록이 아니라, **그날 의미 있는 신호가 잡힌 종목 리스트**라고 보면 됩니다.

---

## 현재 실행 주기

GitHub Actions workflow는 아래 파일에 있습니다.

```text
.github/workflows/update-signals.yml
```

현재 자동 실행 주기는 **1시간마다 한 번**입니다.

```yaml
schedule:
  - cron: "0 * * * *"
```

GitHub Actions의 cron은 UTC 기준입니다. 즉 매시 정각에 실행됩니다.

```text
00:00 UTC
01:00 UTC
02:00 UTC
...
```

수동 실행도 가능합니다.

```text
GitHub repo → Actions → Update signal scan → Run workflow
```

수동 실행하면 바로 한 번 스캐너가 돌고, 성공하면 CSV가 생성되거나 갱신됩니다.

---

## 전체 파일 흐름

```text
GitHub Actions 실행
        ↓
requirements.txt로 필요한 패키지 설치
        ↓
puddle_rsi_signal_scanner.py 실행
        ↓
스캔 대상 티커 목록 준비
        ↓
Yahoo Finance 가격 데이터 다운로드
        ↓
MA20 / MA60 / MA120 / MA200 / RSI 계산
        ↓
Puddle 조건 확인
        ↓
신호 발생 종목만 결과 DataFrame으로 정리
        ↓
signal_scans/signal_scan_YYYYMMDD.csv 저장
        ↓
GitHub repo에 자동 commit / push
```

---

## 현재 주요 파일

| 파일 / 폴더 | 역할 |
|---|---|
| `puddle_rsi_signal_scanner.py` | 실제 스캐너 코드. 티커 준비, 가격 다운로드, 지표 계산, 신호 판정, CSV 저장을 담당합니다. |
| `.github/workflows/update-signals.yml` | GitHub Actions 자동 실행 설정입니다. 1시간마다 스캐너를 실행합니다. |
| `requirements.txt` | GitHub Actions와 로컬 실행에 필요한 Python 패키지 목록입니다. |
| `signal_scans/` | 날짜별 스캔 결과 CSV가 저장되는 폴더입니다. |
| `README.md` | 현재 문서입니다. |

현재는 Streamlit 화면 파일을 제거했습니다. 나중에 대시보드가 필요해지면 새로 만들면 됩니다.

---

## 스캔 대상

현재 스캔 대상은 복잡한 시총 전체 랭킹 방식이 아니라, **대형주와 대표 ETF를 단순하고 안정적으로 커버하는 방식**으로 구성되어 있습니다.

### 1. Stock universe

주식은 아래 두 그룹을 합친 뒤 중복을 제거합니다.

```text
S&P 500 상위 100개
+
NASDAQ 100 구성종목
```

즉 미국 대표 대형주와 나스닥 대표 성장주를 같이 봅니다.

예를 들어:

```text
AAPL
MSFT
NVDA
AMZN
META
AVGO
COST
ADBE
PEP
AMD
```

같은 종목들이 포함될 수 있습니다.

같은 종목이 S&P 500 상위 100과 NASDAQ 100에 모두 있으면 한 번만 스캔합니다.

CSV에는 `universe` 컬럼으로 출처가 표시됩니다.

```text
S&P500
NASDAQ100
S&P500,NASDAQ100
```

예시:

| ticker | universe | 의미 |
|---|---|---|
| AAPL | `S&P500,NASDAQ100` | S&P 500 상위권에도 있고 NASDAQ 100에도 있는 핵심 대형주 |
| ADBE | `NASDAQ100` | NASDAQ 100 쪽 대표 성장주 |
| UNH | `S&P500` | S&P 500 대형주 쪽 종목 |

### 2. ETF universe

ETF는 ETFDB 같은 외부 사이트를 매번 긁어오는 방식이 아니라, 코드 안에 정의된 대표 ETF 목록을 사용합니다.

이유는 ETFDB가 GitHub Actions 서버 요청을 막는 경우가 있었기 때문입니다.

현재 ETF universe는 대략 이런 종류를 포함합니다.

```text
SPY, IVV, VOO, VTI, QQQ
채권 ETF: AGG, BND, TLT, IEF, SHY, LQD, HYG
섹터 ETF: XLK, XLV, XLF, XLE, XLY, XLI, XLP, XLU, XLB
반도체 ETF: SMH, SOXX
금/원자재 ETF: GLD, SLV, USO
해외 ETF: VEA, VWO, EFA, EEM, EWJ, EWZ, FXI
```

즉 최신 ETF 시총 랭킹을 매번 가져오는 구조는 아니지만, 대표성이 높은 ETF들을 안정적으로 스캔합니다.

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

예를 들어 2026년 5월 12일에는 아래 파일이 하루 동안 계속 갱신됩니다.

```text
signal_scans/signal_scan_20260512.csv
```

다음 날이 되면 새 파일이 생성됩니다.

```text
signal_scans/signal_scan_20260513.csv
```

이 구조를 쓰는 이유는 다음과 같습니다.

```text
루트 폴더를 지저분하게 만들지 않기 위해
날짜별 이력을 남기기 위해
나중에 CSV를 모아서 공부하거나 분석하기 쉽게 하기 위해
```

---

## CSV에는 무엇이 들어가나?

출력 CSV에는 전체 스캔 대상 종목이 모두 들어가지 않습니다.

저장되는 것은 아래 조건 중 하나를 만족한 종목뿐입니다.

```text
Puddle 신호 발생
또는
RSI & Puddle 신호 발생
```

즉 신호가 없는 종목은 CSV에 없습니다.

CSV 컬럼은 다음과 같습니다.

| 컬럼 | 설명 |
|---|---|
| `scan_timestamp_utc` | 스캐너가 실행된 UTC 기준 시각입니다. |
| `date` | 실제 가격 데이터 기준 날짜입니다. 주말이나 장 휴장일이면 가장 가까운 이전 거래일 데이터가 사용될 수 있습니다. |
| `asset_type` | `Stock` 또는 `ETF`입니다. |
| `universe` | 종목이 어느 universe에서 왔는지 표시합니다. 예: `S&P500`, `NASDAQ100`, `S&P500,NASDAQ100`, `ETF` |
| `ticker` | 종목 티커입니다. |
| `signal` | 최종 신호입니다. `Puddle` 또는 `RSI & Puddle` 값이 들어갑니다. |
| `close` | 해당 날짜 종가입니다. |
| `change_pct` | 전일 대비 등락률입니다. 단위는 %입니다. |
| `rsi` | 14일 RSI 값입니다. |
| `puddle` | 발생한 Puddle 단계와 설명입니다. |

예시:

```csv
scan_timestamp_utc,date,asset_type,universe,ticker,signal,close,change_pct,rsi,puddle
2026-05-12T18:00:00+00:00,2026-05-12,Stock,"S&P500,NASDAQ100",AAPL,Puddle,182.15,-1.42,41.23,"1st: MA20, 10% cash"
2026-05-12T18:00:00+00:00,2026-05-12,ETF,ETF,QQQ,RSI & Puddle,421.88,-2.71,29.84,"4th: MA200, RSI<=30, 100% cash, 40d"
```

---

## 사용하는 가격 데이터

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

스캐너는 종가 기준으로 이동평균선과 RSI를 계산합니다.

---

## 참고로 함께 가져오는 시장 데이터

스캐너는 아래 시장 데이터도 함께 가져올 수 있도록 되어 있습니다.

| 항목 | 티커 | 의미 |
|---|---|---|
| 10Y Treasury | `^TNX` | 미국 10년물 금리 |
| VIX | `^VIX` | 변동성 지수 |
| VIX1D | `^VIX1D` | 1일 변동성 지수 |
| SKEW | `^SKEW` | 꼬리위험 / 극단적 리스크 참고 지표 |

현재 최종 CSV에는 핵심 신호 결과만 저장합니다. 위 데이터는 내부 계산 및 향후 확장용으로 활용할 수 있습니다.

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
Change(%) = (오늘 종가 / 전일 종가 - 1) × 100
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

각각 최근 20일, 60일, 120일, 200일 평균 종가입니다.

초보자 관점에서 쉽게 말하면:

```text
MA20  = 단기 흐름
MA60  = 중기 흐름
MA120 = 중장기 흐름
MA200 = 장기 추세
```

Puddle은 가격이 이 이동평균선 아래로 내려가는 순간을 감지합니다.

### RSI

기본 14일 RSI를 계산합니다.

```text
RSI window = 14
```

RSI는 최근 가격 상승/하락 강도를 숫자로 보여주는 지표입니다.

일반적으로:

```text
RSI 70 이상 = 과열 가능성
RSI 30 이하 = 과매도 가능성
```

이 프로젝트에서는 RSI가 30 이하일 때 더 강한 신호로 봅니다.

---

## Puddle 신호란?

이 프로젝트에서 Puddle은 가격이 중요한 이동평균선을 위에서 아래로 이탈하는 상황을 의미합니다.

단순히 가격이 이동평균선 아래에 있는 모든 경우를 잡는 것이 아닙니다.

아래처럼 **전날에는 이동평균선 위에 있었는데, 오늘 아래로 내려온 순간**을 봅니다.

```text
전일 종가 >= 전일 이동평균선
오늘 종가 < 오늘 이동평균선
```

즉 Puddle은 “이미 약한 상태” 전체를 찾는 신호라기보다, **추세가 한 단계 꺾이는 순간**을 잡는 신호입니다.

---

## Puddle 단계

### 1st Puddle

단기선인 MA20 아래로 내려온 경우입니다.

```text
오늘 종가 < MA20
전일 종가 >= 전일 MA20
```

출력 문구:

```text
1st: MA20, 10% cash
```

해석:

```text
단기 흐름이 약해지기 시작한 상태
```

### 2nd Puddle

중기선인 MA60 아래로 내려온 경우입니다.

```text
오늘 종가 < MA60
전일 종가 >= 전일 MA60
```

출력 문구:

```text
2nd: MA60, 50% cash, 5d
```

해석:

```text
중기 흐름까지 약해진 상태
```

### 3rd Puddle

중장기선인 MA120 아래로 내려온 경우입니다.

```text
오늘 종가 < MA120
전일 종가 >= 전일 MA120
```

출력 문구:

```text
3rd: MA120, 50% cash, 5d
```

해석:

```text
중장기 추세에 경고가 들어온 상태
```

### 4th Puddle

장기선인 MA200 아래로 내려오고, 동시에 RSI도 30 아래인 경우입니다.

```text
오늘 종가 < MA200
전일 종가 >= 전일 MA200
RSI < 30
```

출력 문구:

```text
4th: MA200, RSI<=30, 100% cash, 40d
```

해석:

```text
장기 추세 이탈 + 과매도 구간이 동시에 발생한 강한 경고 상태
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
| `Puddle` | Puddle 조건이 발생한 종목입니다. |
| `RSI & Puddle` | Puddle 조건이 발생했고, 동시에 RSI가 30 이하인 종목입니다. |

중요한 점은 `RSI & Puddle`이 단순 RSI 과매도 종목이 아니라는 것입니다.

```text
RSI만 낮음 → 저장 안 됨
Puddle만 발생 → Puddle
Puddle 발생 + RSI <= 30 → RSI & Puddle
```

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

## GitHub Actions가 실패할 수 있는 이유

이 프로젝트는 외부 데이터를 가져오기 때문에 가끔 실패할 수 있습니다.

대표적인 원인은 다음과 같습니다.

```text
Yahoo Finance rate limit
Slickcharts 또는 Wikipedia 테이블 구조 변경
네트워크 일시 오류
GitHub Actions runner 일시 문제
```

ETFDB는 GitHub Actions에서 403 Forbidden이 발생할 수 있어 현재 사용하지 않습니다. 대신 코드 내부의 대표 ETF 목록을 사용합니다.

---

## 로컬 실행 방법

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

직접 만든 종목 리스트를 사용하려면:

```bash
python puddle_rsi_signal_scanner.py \
  --stocks-csv stocks.csv \
  --etfs-csv etfs.csv
```

CSV 예시:

```csv
ticker
AAPL
MSFT
SPY
QQQ
```

---

## 현재 완성된 기능

```text
1시간마다 자동 실행
S&P 500 상위 100 + NASDAQ 100 통합 주식 universe
대표 ETF 고정 universe
중복 ticker 제거
Yahoo Finance 가격 데이터 다운로드
MA20 / MA60 / MA120 / MA200 계산
RSI 계산
Puddle / RSI & Puddle 신호 탐지
날짜별 CSV 저장
GitHub repo 자동 커밋
Yahoo Finance 캐시 사용
```

---

## 향후 확장 후보

나중에 확장할 수 있는 기능은 다음과 같습니다.

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

현재는 그 전에 먼저 자동 스캔과 CSV 이력 저장이 안정적으로 되는 것을 목표로 합니다.
