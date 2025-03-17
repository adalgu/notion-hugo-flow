---
author: Gunn Kim
date: '2025-03-16T19:10:00.000Z'
draft: true
keywords: &id001
- Uncategorized
lastmod: '2025-03-16T19:10:00.000Z'
notion_id: 1b87522e-eb2f-817a-9471-f218efab360d
tags: *id001
title: '[SQL] 데이터 기간 한정 할때 between이 시간일 경우 범위는 어떻게 되나?'
---


10시에서 12시 사이에 발생한 데이터를 뽑는다고 할때,


SELECT *

FROM MYDB

WHERE hour between 10 and 12


하면 된다.


그런데, 이렇게 뽑은 데이터에는 12시 10분 데이터가 포함될 것인가?

12시 정각이 넘은 데이터는 빠지는가?


정답은? 포함된다.


가끔씩 헷갈려서 적어둠.

이상.

