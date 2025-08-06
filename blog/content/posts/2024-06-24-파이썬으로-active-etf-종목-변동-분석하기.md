---
author: Gunn Kim
date: '2024-06-24'
description: 이 포스트에서는 파이썬을 사용하여 Active ETF의 종목 변동을 분석하는 방법을 소개합니다. 타임폴리오 자산운용의 '타임폴리오
  코리아 플러스배당액티브 ETF'를 예시로 데이터 수집, 분석, 시각화를 통해 매니저의 투자 전략을 파악하는 방법을 배워보세요.
draft: false
keywords: &id001
- Python
- 투자
- ETF
- 데이터분석
lastmod: '2025-04-04T09:47:00.000Z'
notion_id: 80bce9f9-67e4-4e65-8470-6f9eaf18f546
slug: analyzing-active-etf-with-python
subtitle: '타임폴리오 코리아 플러스배당액티브 ETF를 예시로 종목 비중 변화를 분석해보자**

  **'
summary: 이 포스트에서는 파이썬을 사용하여 Active ETF의 종목 변동을 분석하는 방법을 소개합니다. 타임폴리오 자산운용의 '타임폴리오
  코리아 플러스배당액티브 ETF'를 예시로 데이터 수집, 분석, 시각화를 통해 매니저의 투자 전략을 파악하는 방법을 배워보세요.
tags: *id001
title: 파이썬으로 Active ETF 종목 변동 분석하기
---


안녕하세요, 파이썬으로 금융 문제를 해결해 보는 블로그에 오신 것을 환영합니다! 오늘은 Active ETF의 종목 변동을 파이썬으로 분석하는 방법을 소개하려고 합니다. 이 글을 통해 여러분은 ETF 매니저가 어떤 종목의 비중을 늘리고 줄였는지, 그 이유가 무엇인지 파악할 수 있습니다.

## Active ETF란 무엇인가요?

먼저, Active ETF에 대해 간단히 설명드릴게요. ETF(Exchange Traded Fund)는 주식처럼 거래되는 펀드입니다. Active ETF는 매니저가 시장 상황에 따라 종목을 적극적으로 조정하는 ETF를 말합니다. 따라서 어떤 종목의 비중이 어떻게 변했는지를 분석하면 매니저의 투자 전략을 엿볼 수 있죠.

## 왜 타임폴리오 액티브 ETF인가요?

이번 분석에서는 타임폴리오자산운용의 '타임폴리오 코리아 플러스배당액티브 ETF'를 예시로 사용했습니다. 이 ETF는 최근 업계 최초로 특별배당을 실시하며 주목받고 있습니다.

타임폴리오자산운용은 2024년 6월, 이 ETF가 1%의 특별배당을 시행한다고 발표했습니다. 이는 기존 월배당 0.5%에 추가된 것으로, 총 1.5%의 배당금을 지급하게 됩니다. 타임폴리오 코리아 플러스배당액티브 ETF는 삼양식품, SK하이닉스와 같은 실적이 좋은 주도주와 현대차, 메리츠금융지주 등 주주 친화적인 고배당주를 적절히 편입하여 우수한 성과를 달성하고 있습니다.

타임폴리오의 조상준 부장은 이 ETF가 상승장과 하락장 모두에서 시장을 이기는 투자를 할 수 있다고 강조했습니다. 이 ETF는 최근 연간 수익률 43.1%를 기록하며 전체 배당 ETF 중 수익률 1위를 달성했습니다. 배당 수익뿐만 아니라 자본차익까지 노리는 적극적인 종목선별 전략 덕분에 이러한 성과를 이룰 수 있었습니다.

특히 삼양식품의 경우, 주가가 급등하는 동안 ETF의 주요 종목으로 편입되었고, 이는 전체 수익률을 크게 높이는 데 기여했습니다. 이러한 이유로 우리는 이 ETF를 예시로 선택하여 종목 변동을 분석해보려 합니다.

## 필요한 도구들

이 분석을 위해 필요한 도구는 간단합니다:

- `requests`: 웹에서 데이터를 가져오기 위한 라이브러리입니다.
- `BeautifulSoup`: HTML 파싱을 위한 라이브러리입니다.
- `pandas`: 데이터 분석을 위한 라이브러리입니다.
- `matplotlib`: 데이터 시각화를 위한 라이브러리입니다.
이제 코드를 작성해볼까요?

## 데이터 수집

먼저, 특정 기간 동안 Active ETF의 종목 데이터를 수집해야 합니다. 이를 위해 웹에서 데이터를 가져오고, `BeautifulSoup`으로 파싱하여 `pandas` DataFrame으로 저장할 겁니다.

```python
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# 한글 폰트 설정
font_path = '/System/Library/Fonts/Supplemental/AppleGothic.ttf'  # 또는 적절한 폰트 경로 지정
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font_name)
plt.rcParams['axes.unicode_minus'] = False


def get_etf_data(start_date, end_date):
    # 시작일과 종료일을 datetime 객체로 변환
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    # 수집한 데이터를 저장할 리스트 초기화
    data = []

    # 시작일부터 종료일까지 하루씩 증가시키며 데이터 수집
    current_date = start_date
    while current_date <= end_date:
        # 날짜를 문자열로 변환
        search_date = current_date.strftime("%Y-%m-%d")
        print(f"Fetching data for {search_date}")

        # 요청할 URL 및 파라미터 설정
        url = "<https://www.timefolio.co.kr/etf/funds_pdf_view.php?PID=13>"
        params = {
            "search_date": search_date
        }
        response = requests.post(url, data=params)

        if response.status_code == 200:
            response.encoding = 'utf-8'  # 인코딩 설정
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find("table", {"class": "tblArea type_center"})
            if table:
                rows = table.find("tbody").find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) == 5:  # NO 열 제외
                        try:
                            data.append({
                                "기준일자": search_date,
                                "종목명": cols[0].text.strip(),
                                "종목코드": cols[1].text.strip(),
                                "수량": float(cols[2].text.strip().replace(',', '')),
                                "비중(%)": float(cols[3].text.strip()),
                                "평가금액(원)": float(cols[4].text.strip().replace(',', ''))
                            })
                        except ValueError as e:
                            print(f"ValueError for {search_date} - {cols[0].text.strip()}: {e}")
        else:
            print(f"Failed to fetch data for {search_date}")

        # 하루 증가
        current_date += timedelta(days=1)
        print(f"Completed fetching data for {search_date}")

    # 수집한 데이터를 DataFrame으로 변환
    df = pd.DataFrame(data)
    print("Data fetching complete. Converting to DataFrame.")
    return df


# 사용 예시
start_date = "2024-06-01"
end_date = "2024-06-18"
df = get_etf_data(start_date, end_date)

# 데이터 저장
df.to_csv("etf_data.csv", index=False)
print("Data saved to etf_data.csv")

```

위 코드는 지정된 기간 동안 매일 Active ETF의 종목 데이터를 가져옵니다. 가져온 데이터를 `etf_data.csv` 파일로 저장합니다.

## 데이터 분석

이제 수집한 데이터를 분석하여 각 종목의 비중 변동을 살펴보겠습니다.

```python
# 데이터 로드
df = pd.read_csv("etf_data.csv")

# 비중 변동 분석
df['기준일자'] = pd.to_datetime(df['기준일자'])
pivot_df = df.pivot_table(index='기준일자', columns='종목명', values='비중(%)', aggfunc='mean')

# 수량 및 평가금액 변동 분석
df['수량변동'] = df.groupby('종목명')['수량'].diff().fillna(0)
df['평가금액변동'] = df.groupby('종목명')['평가금액(원)'].diff().fillna(0)

# 비중 변동
df['비중변동'] = df.groupby('종목명')['비중(%)'].diff().fillna(0)

# 결과 분석
result = df.groupby('종목명').agg({
    '수량변동': 'sum',
    '평가금액변동': 'sum',
    '비중변동': 'sum'
}).sort_values(by='비중변동', ascending=False)

# 결과 출력
print(result)

```

이 코드는 각 종목의 비중 변동, 수량 변동, 평가금액 변동을 계산하고 이를 출력합니다. 이를 통해 어떤 종목의 비중이 어떻게 변했는지 알 수 있습니다.

## 데이터 시각화

마지막으로, 데이터를 시각화하여 각 종목의 비중 변화를 그래프로 확인해보겠습니다.

```python
# DataFrame을 시각화하여 종목별 비중 변화 추이 확인
plt.figure(figsize=(14, 7))
for stock in pivot_df.columns:
    plt.plot(pivot_df.index, pivot_df[stock], label=stock)

plt.title('종목별 비중 변화 추이')
plt.xlabel('기준일자')
plt.ylabel('비중(%)')
plt.legend(loc='upper right')
plt.show()

```

이 그래프를 통해 각 종목의 비중이 시간에 따라 어떻게 변했는지를 한눈에 확인할 수 있습니다.

## 결론

오늘은 파이썬을 사용하여 Active ETF의 종목 변동을 분석하는 방법을 배웠습니다. 수집한 데이터를 바탕으로 매니저의 투자 전략을 파악하고, 종목의 비중 변동이 의도된 것인지, 아니면 시장 가격 변동 때문인지를 분석할 수 있습니다.

예를 들어, 삼양식품처럼 주가가 급등한 종목의 경우, 비중 변동만으로는 펀드매니저의 의사결정을 정확히 파악하기 어렵습니다. 이러한 이유로 수량 변동과 평가금액 변동을 함께 분석하는 것이 중요합니다. 다음 포스트에서는 이 부분을 더 깊이 있게 다룰 예정이니 기대해주세요!

궁금한 점이 있으면 언제든지 의견 남겨주세요. 다음 포스트에서 또 만나요!


