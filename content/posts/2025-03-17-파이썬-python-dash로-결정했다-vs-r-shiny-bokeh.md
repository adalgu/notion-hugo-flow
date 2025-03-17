---
author: Gunn Kim
date: '2025-03-16T19:05:00.000Z'
draft: true
keywords: &id001
- Uncategorized
lastmod: '2025-03-16T19:05:00.000Z'
notion_id: 1b87522e-eb2f-81b5-b986-cddf9c3e6eb7
subtitle: 웹 대시보드를 만들어 보자
tags: *id001
title: '[파이썬] Python Dash로 결정했다 (vs. R Shiny, Bokeh)'
---

![](https://miro.medium.com/max/800/1*rRlAWnRIFf2Ti_bIXzMFSg.gif)

> 이런 대시보드가 만들고 싶었다. -보드 한닢- ~~(동전한닢)~~

회사를 옮기고 부터는 파이썬에 익숙해졌다. 이전에는 Eviews와 Stata에서 R로 데이터를 다루었는데, 여기서는 파이썬이 메인툴이 되었다.

R이냐 파이썬이냐의 선택때문에 무한 고민을 했던 것이 엊그제 같은데, R로 시작하니 R만 보였다가, 이제는 R Studio를 거의 켜지 않는 지경에 이르렀다. 파이썬을 시작하니 이것 나름대로 엄청나게 잘 구축된 생태계가 있기에 또 언제그랬냐는듯 익숙해진다.

R의 최대 강점인 데이터프레임을 파이썬 판다스에서 거의 완벽하게 재현하고 있다는 것이 R에서 파이썬으로 부담없이 이동할 수 있었던 것 같다.

나중에 한번 포스팅을 하겠지만,

* 엑셀의 Pivot, R의 데이터프레임(groupby 연산), 파이썬의 Pandas

위 세개가 데이터분석에 있어서는 기본 중의 기본인것 같다. ~~고 생각한다~고로 존재한다~~

***

암튼 파이썬으로 이런 저런 작업을 하면서 SQL 쿼리로 데이터를 부르거나, 오픈API로 데이터를 불러오거나, 크롤링으로 웹 데이터를 긁어오고, 이런 데이터를 판다스로 담고 시각화하고 분석하는 것은 이래저래 해본 것 같다.

그러다 보니 이제 이런 데이터를 대시보드에 올려서 웹으로 공유하는 단계에 접어들고 있다. R로 정적 웹사이트를 만들면서, [별도로 Rmarkdown 웹페이지를 운영해보려고 했던 시도](https://gunn.kim/post/2018-12-21-hugo-vs-blogdown/)가 결국 인터랙티브한 웹사이트를 구현해 보는 것이었는데, 결국 대시보드로 귀결되고 있는 것이다.

R에서는 이미 Shiny가 거의 평정한 것으로 알고 있었는데, 파이썬에서는 무엇이 있는지 잠시 찾아본 결과, **대시(Dash)** 를 이용해 보기로 결론을 내렸다. 대시를 이용해 보기로 한 것은 아래 글을 참고한 결과다.

* 'Shiny vs. Dash: A Side-by-side comparison' : [https://www.r-bloggers.com/shiny-vs-dash-a-side-by-side-comparison/](https://www.r-bloggers.com/shiny-vs-dash-a-side-by-side-comparison/ "https://www.r-bloggers.com/shiny-vs-dash-a-side-by-side-comparison/")
* 'Bokeh vs Dash — Which is the Best Dashboard Framework for Python?' : [https://www.sicara.ai/blog/2018-01-30-bokeh-dash-best-dashboard-framework-python](https://www.sicara.ai/blog/2018-01-30-bokeh-dash-best-dashboard-framework-python "https://www.sicara.ai/blog/2018-01-30-bokeh-dash-best-dashboard-framework-python")

To be continued...

