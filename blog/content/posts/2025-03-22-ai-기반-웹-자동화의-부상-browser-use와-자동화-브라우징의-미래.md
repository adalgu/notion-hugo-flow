---
author: Gunn Kim
date: '2025-03-22'
description: AI가 웹 브라우저를 제어하는 시대가 열렸습니다. Manus가 채택한 Browser Use와 유사 프로젝트 AgenticReplay를
  비교하며 AI 기반 웹 자동화의 현재 기술 수준과 미래 발전 가능성을 탐구합니다. Selenium과 Playwright 기반 접근 방식의 차이점,
  AI 통합의 중요성, 그리고 Realtime API 연동 등 확장 아이디어를 제시합니다.
draft: false
keywords: &id001
- AI
- Web Automation
- Browser
lastmod: '2025-06-22T03:36:00.000Z'
notion_id: 1be7522e-eb2f-807e-b828-de0a80e9c3a3
slug: ai-web-automation-browser-use
subtitle: 'AI 기반 웹 자동화의 부상: Browser Use와 AgenticReplay 비교 분석 및 미래 전망'
summary: AI가 웹 브라우저를 제어하는 시대가 열렸습니다. Manus가 채택한 Browser Use와 유사 프로젝트 AgenticReplay를
  비교하며 AI 기반 웹 자동화의 현재 기술 수준과 미래 발전 가능성을 탐구합니다. Selenium과 Playwright 기반 접근 방식의 차이점,
  AI 통합의 중요성, 그리고 Realtime API 연동 등 확장 아이디어를 제시합니다.
tags: *id001
title: 'AI 기반 웹 자동화의 부상: Browser Use와 자동화 브라우징의 미래'
---

## **서론**

최근 AI 기술의 발전으로 웹 자동화 분야에 혁신적인 변화가 일어나고 있습니다. 특히 Browser Use라는 프로젝트가 Manus를 통해 세계적인 주목을 받게 되었습니다. 이는 AI가 웹 브라우저를 직접 제어하고 복잡한 작업을 수행할 수 있는 능력을 보여주는 중요한 사례입니다.

저는 이전에 AgenticReplay라는 유사한 컨셉의 프로젝트를 구상하고 구현을 준비했었습니다. 그러나 Browser Use가 완성도 높게 출시되면서 이 분야에 큰 변화가 일어났습니다. 이 블로그 포스트에서는 두 프로젝트를 비교하고, AI 기반 웹 자동화의 현재와 미래에 대해 살펴보겠습니다.

## **1. AgenticReplay 비전**

![AgenticReplay 아키텍처 개요 - Selenium 기반 웹 자동화 시스템의 구조도. 이벤트 추적 모듈, 데이터 관리 모듈, 이벤트 재현 모듈이 상호 연결된 다이어그램]

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/94f51666-273a-443d-bf89-42827b5b6876/f0220c66-20a2-4c4c-89ad-2a38d7b5bd57/image.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466U4SWP46A%2F20250622%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20250622T034013Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEPj%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJGMEQCIFxkHI3e87yLGKKwuIqTh09nlMzjQXN13J88SMFHrLvSAiB%2F40kzpuceOOFouQZoGVp3UXOAVQPqVXB4bxernm3hYCqIBAjh%2F%2F%2F%2F%2F%2F%2F%2F%2F%2F8BEAAaDDYzNzQyMzE4MzgwNSIMYLplJ5RtnPESVvpjKtwDmIY6Nd1JMiA61UnzySg4jPExIr7EfXrrwWihiQpRyxwXZCQTH3RCikxUBolZcTLKZnLq05RhFGx1ajeeNWEgI4W4SN3eWKfz9bPPcAn0FSKAFVdDEjaSjqh2uvh8HQOh925Hbc1hxWhXDT32DQRQEvapmJLq1aSvBa0IDdZTfXR7rtQyJcsOhMrVtJwWEzcEJXzYu%2FhZetXolpg2zsDWQ5qOYIGRKUKH9y9Bf8Mpy%2B2qkqWVebTJ71PeluGIss7rkJrKh57al2mQLvo5H3Xr2%2FLs%2F%2BSR551twDiEKWV%2B9%2Bkf4X%2BVHL5XjGYgLUjrtRwuZ%2Fwh1SGiwZPhoX9YsHUaNe9%2F84uRz5ISnBHche83zqP85oSfdy%2FP%2Bo7GCAra1lROjMcF8o099iFv6XwCrjCsRu2JFr9Qf4Iz7lnt32bvIvkY%2BNqS9LMCMbzkWl5tUhs39Q0wJpokiDEbEdLEiSk3YPUpD16oHTGf0rW3ylppteWT8HRlZvuqGQdE7QahtJ19JnYAPuHg9Vuc5uvt5mOUSbVq4I6MJcRSfLrCjOsnsDicgK6uDkktIpVQvaVhH4kzhTOI%2FlBSWm5ki5LLI1zzUK5bulRXdzv%2Bw9lCYLnrTZfY0MNHslg6iJned%2Fow7YfdwgY6pgF2gCUiEn8y7rD4F4sLNzTkuoCkF7EbUeGb2FMeJabTp7nMgSu7ahGnWLSZKiz2U05yLDnTsDzricjoMNU8z%2BOZ8gumpuXXibEO%2BBhcCi6jsFbPEtbrcNfiBpJggqVBXPbLNs9Kf%2BYRhPVDbHXsZZ%2FE7qNU%2F%2BZak4ptANautT%2FstazCh%2BAN1dG0855nFQ8WmvilJgLzBgVUMP1CWVRdenYNA1mRvYUX&X-Amz-Signature=ba374a50e204348c1abeb700d9b7b53f95022ad1bddf72079ba8744ca21a9b1e&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

### **프로젝트 개념 및 목표**

AgenticReplay는 Selenium을 활용하여 웹사이트 자동화를 목표로 하는 프로젝트였습니다. 이 프로젝트의 핵심 아이디어는 사용자가 웹사이트에서 수행하는 행동을 추적하고, 이를 기록한 후 필요할 때 재현하는 것이었습니다. 이를 통해 반복적인 웹 작업을 자동화하고, 프로토타입 개발 및 테스트 효율을 높이는 것이 주요 목표였습니다.

### **Selenium을 활용한 아키텍처 및 접근 방식**

AgenticReplay는 다음과 같은 구조로 설계되었습니다:

1. **이벤트 추적 모듈(event_tracker)**: Selenium을 사용하여 사용자의 웹 상호작용을 추적하고 기록합니다.
1. **데이터 관리 모듈(data_manager)**: 추적된 이벤트를 저장하고 관리합니다.
1. **이벤트 재현 모듈(event_replayer)**: 저장된 데이터를 기반으로 웹 상호작용을 재현합니다.
이 접근 방식은 Selenium의 강력한 웹 자동화 기능을 활용하여 다양한 웹사이트에서 작동할 수 있는 범용성을 목표로 했습니다.

### **계획된 기능 및 구현 로드맵**

AgenticReplay는 13주에 걸친 개발 계획을 가지고 있었으며, 다음과 같은 주요 단계로 구성되었습니다:

1. 프로젝트 초기화 및 환경 설정 (1주차)
1. 이벤트 추적 기능 개발 (2-3주차)
1. 이벤트 재현 기능 개발 (4-5주차)
1. 데이터 관리 시스템 구축 (6-7주차)
1. 사용자 인터페이스 개발 (8-9주차)
1. 통합 및 테스트 (10-11주차)
1. 문서화 및 최종 점검 (12주차)
1. 배포 및 유지보수 (13주차 이후)
이 로드맵은 체계적인 개발 과정을 통해 완성도 높은 웹 자동화 도구를 구축하는 것을 목표로 했습니다.

## **2. Browser Use: 브라우저 자동화의 혁신**

### **Browser Use 프로젝트 개요**

Browser Use는 AI 에이전트가 브라우저를 제어할 수 있게 해주는 혁신적인 도구입니다. 이 프로젝트는 Python 기반으로 개발되었으며, 다양한 AI 모델(GPT-4o, Claude, Gemini 등)과 연동하여 웹 브라우저를 자동화할 수 있습니다. 특히 주목할 점은 사용 편의성으로, 간단한 설치와 설정만으로도 강력한 브라우저 자동화 기능을 활용할 수 있습니다.

### **주요 기능 및 기술적 혁신**

Browser Use의 주요 기능은 다음과 같습니다:

1. **다양한 AI 모델 지원**: OpenAI, Anthropic, Google 등 다양한 AI 제공업체의 모델을 지원합니다.
1. **DOM 추출 및 분석**: 웹페이지의 DOM 구조를 분석하여 상호작용 가능한 요소를 식별합니다.
1. **복잡한 작업 자동화**: 로그인, 양식 작성, 검색, 쇼핑 등 다양한 웹 작업을 자동화할 수 있습니다.
1. **멀티탭 지원**: 여러 탭을 동시에 관리하고 작업할 수 있습니다.
1. **커스텀 함수 확장**: 사용자 정의 함수를 통해 기능을 확장할 수 있습니다.
### **AI 기반 브라우저 제어 구현 방식**

Browser Use는 다음과 같은 구조로 구현되어 있습니다:

1. **Agent**: 사용자의 작업을 이해하고 계획을 수립하는 AI 에이전트
1. **Browser**: 실제 브라우저와 상호작용하는 모듈
1. **DOM**: 웹페이지의 구조를 분석하고 상호작용 가능한 요소를 식별하는 모듈
1. **Controller**: 에이전트와 브라우저 간의 통신을 관리하는 모듈
이 구조는 AI 모델이 웹페이지를 이해하고 적절한 행동을 취할 수 있도록 설계되었습니다.

### **웹 요소 감지 기능 분석**

![Browser Use의 웹 요소 감지 기능 - 웹페이지에서 상호작용 가능한 요소들이 자동으로 식별되고 인덱스가 부여된 스크린샷. 버튼, 입력 필드, 링크 등이 경계 상자로 표시되어 있음]

Browser Use의 가장 인상적인 기능 중 하나는 웹 요소 감지 능력입니다. 웹사이트에 접속하면 상호작용 가능한 요소(버튼, 입력 필드, 링크 등)를 자동으로 식별하고, 각 요소에 인덱스를 부여합니다. 이를 통해 AI 에이전트는 정확하게 타겟팅하여 액션을 수행할 수 있습니다. 마치 객체 감지(object detection) 기술처럼 웹 요소를 인식하는 이 기능은 웹 자동화의 정확성과 효율성을 크게 향상시킵니다.

```python
# Browser Use의 요소 감지 및 상호작용 예시 코드from browser_use import Agent
from langchain_openai import ChatOpenAI

agent = Agent(
    task="로그인 후 대시보드에서 최신 보고서 다운로드",
    llm=ChatOpenAI(model="gpt-4o"),
)
await agent.run()

# 내부적으로 Browser Use는 다음과 같은 방식으로 요소를 식별하고 상호작용함:# 1. DOM 분석을 통해 상호작용 가능한 요소 식별# 2. 각 요소에 인덱스 부여 (예: [1]<button>로그인</button>)# 3. AI가 컨텍스트를 이해하고 적절한 요소와 상호작용
```

## **3. 기술적 비교**

### **두 접근 방식 간의 아키텍처 차이점**

AgenticReplay와 Browser Use는 모두 웹 자동화를 목표로 하지만, 접근 방식에 중요한 차이가 있습니다:

1. **기반 기술**: AgenticReplay는 Selenium을 기반으로 하는 반면, Browser Use는 Playwright를 활용합니다.
1. **AI 통합**: AgenticReplay는 전통적인 자동화 스크립트 접근 방식을 취하는 반면, Browser Use는 AI 모델을 핵심 구성 요소로 통합했습니다.
1. **구조적 복잡성**: AgenticReplay는 이벤트 추적, 데이터 관리, 이벤트 재현이라는 세 가지 주요 모듈로 구성된 반면, Browser Use는 에이전트, 브라우저, DOM, 컨트롤러 등 더 세분화된 구조를 가지고 있습니다.
### **Browser Use의 구현 이점**

Browser Use는 다음과 같은 구현 이점을 제공합니다:

1. **AI 기반 의사 결정**: 단순한 스크립트 재생이 아닌, AI가 상황을 이해하고 적응적으로 대응합니다.
1. **유연한 작업 처리**: 예상치 못한 상황(팝업, 로딩 지연 등)에 대응할 수 있습니다.
1. **간편한 사용성**: 복잡한 설정 없이도 간단한 Python 코드로 강력한 자동화를 구현할 수 있습니다.
1. **클라우드 지원**: 로컬 설치 외에도 클라우드 버전을 제공하여 접근성을 높였습니다.
### **요소 감지 및 상호작용 기능**

Browser Use의 요소 감지 기능은 특히 인상적입니다. 웹페이지의 DOM을 분석하여 상호작용 가능한 요소를 자동으로 식별하고, 각 요소에 인덱스를 부여합니다. 이를 통해 AI 에이전트는 정확하게 요소를 타겟팅하여 클릭, 텍스트 입력 등의 작업을 수행할 수 있습니다.

반면 AgenticReplay는 Selenium의 요소 선택자(XPath, CSS 선택자 등)를 활용하여 요소를 식별하는 방식을 계획했습니다. 이 방식은 웹사이트 구조가 변경될 경우 스크립트가 실패할 가능성이 높다는 단점이 있습니다.

### **복잡한 웹 시나리오 처리**

![복잡한 웹 시나리오 자동화 - 쇼핑 카트에 상품을 추가하고 결제하는 과정을 Browser Use가 자동으로 수행하는 단계별 스크린샷]

Browser Use는 로그인, 양식 작성, 쇼핑 카트 관리, 다중 탭 작업 등 복잡한 웹 시나리오를 효과적으로 처리할 수 있습니다. 특히 AI 모델의 이해력을 활용하여 웹페이지의 컨텍스트를 파악하고, 적절한 행동을 취할 수 있습니다.

AgenticReplay도 이러한 복잡한 시나리오를 처리하는 것을 목표로 했지만, 사전 정의된 스크립트에 의존하는 방식은 유연성 측면에서 한계가 있었을 것입니다.

## **4. AI 개발에 미치는 영향**

### **Browser Use의 성공이 AI 도구 변화에 주는 시사점**

Browser Use의 성공은 AI가 실제 세계와 상호작용하는 방식에 중요한 변화를 시사합니다. 특히 Manus가 Browser Use를 활용하여 웹 검색을 수행한다는 사실이 알려지면서, AI 에이전트가 웹을 통해 정보를 수집하고 작업을 수행하는 능력이 주목받게 되었습니다.

이는 AI 도구가 단순한 텍스트 생성을 넘어, 실제 웹 환경에서 사용자를 대신하여 작업을 수행할 수 있는 단계로 발전하고 있음을 보여줍니다. 이러한 변화는 AI 개발의 새로운 방향을 제시하고 있습니다.

### **유사한 프로젝트를 개발하는 개발자들에게 미치는 영향**

Browser Use의 성공은 유사한 프로젝트를 개발하는 개발자들에게 중요한 교훈을 제공합니다:

1. **AI 통합의 중요성**: 전통적인 자동화 도구에 AI를 통합하면 더 강력하고 유연한 솔루션을 만들 수 있습니다.
1. **사용자 경험 중심 설계**: 복잡한 기술을 간단한 인터페이스로 제공하는 것이 중요합니다.
1. **확장성 고려**: 다양한 AI 모델과 브라우저를 지원하는 확장 가능한 아키텍처가 필요합니다.
1. **커뮤니티 중심 개발**: Discord 채널 운영, 예제 코드 공유 등 커뮤니티 중심 접근 방식이 프로젝트의 성공에 기여합니다.
### **Realtime API 통합 가능성**

![Realtime API와 Browser Use 통합 개념도 - Browser Use가 다양한 외부 API(날씨, 주식, 뉴스 등)와 실시간으로 연동되어 데이터를 주고받는 아키텍처 다이어그램]

Browser Use와 같은 도구에 Realtime API를 통합하면 더욱 강력한 기능을 구현할 수 있습니다. 실시간 데이터 접근, 외부 서비스와의 연동, 다양한 데이터 소스 활용 등이 가능해집니다. 이는 AI 에이전트가 더 복잡하고 다양한 작업을 수행할 수 있게 해주며, 웹 자동화의 가능성을 크게 확장합니다.

```python
# Realtime API와 Browser Use 통합 예시 코드from browser_use import Agent
from langchain_openai import ChatOpenAI
import realtime_api_client# 가상의 Realtime API 클라이언트# Realtime API 클라이언트 설정
realtime_client = realtime_api_client.Client(api_key="your_api_key")

# 커스텀 함수 정의def get_realtime_stock_data(symbol):
    """실시간 주식 데이터를 가져오는 함수"""
    return realtime_client.get_stock_data(symbol)

def get_weather_forecast(location):
    """실시간 날씨 예보를 가져오는 함수"""
    return realtime_client.get_weather(location)

# Browser Use 에이전트에 커스텀 함수 등록
agent = Agent(
    task="현재 날씨에 따라 적절한 의류 쇼핑몰에서 상품 검색 및 장바구니에 추가",
    llm=ChatOpenAI(model="gpt-4o"),
    custom_functions={
        "get_weather": get_weather_forecast,
        "get_stock_data": get_realtime_stock_data
    }
)
await agent.run()

```

## **5. 미래 가능성**

### **AI 기반 웹 자동화의 향후 발전 방향**

AI 기반 웹 자동화 기술은 다음과 같은 방향으로 발전할 것으로 예상됩니다:

1. **에이전트 메모리 개선**: 요약, 압축, RAG 등을 통해 에이전트의 기억 능력을 향상시킵니다.
1. **계획 능력 강화**: 웹사이트별 컨텍스트를 로드하여 더 효과적인 계획을 수립합니다.
1. **토큰 소비 최적화**: 시스템 프롬프트, DOM 상태 등의 토큰 소비를 줄입니다.
1. **DOM 추출 개선**: 날짜 선택기, 드롭다운 등 특수 요소에 대한 추출 기능을 개선합니다.
1. **작업 재실행 기능**: LLM을 폴백으로 활용하고, 워크플로우 템플릿을 정의하여 재사용성을 높입니다.
### **잠재적인 응용 분야 및 사용 사례**

![AI 웹 자동화의 다양한 응용 분야 - 비즈니스 자동화, 개인 생산성, e-커머스, 콘텐츠 관리, 교육 및 연구, QA 테스팅 등 다양한 영역에서의 활용 사례를 보여주는 인포그래픽]

AI 기반 웹 자동화 기술은 다음과 같은 분야에서 활용될 수 있습니다:

1. **비즈니스 자동화**: 데이터 입력, 보고서 생성, CRM 업데이트 등 반복적인 비즈니스 작업 자동화
1. **개인 생산성**: 이메일 관리, 일정 예약, 정보 수집 등 개인 생산성 향상
1. **e-커머스**: 가격 비교, 제품 검색, 주문 처리 등 쇼핑 관련 작업 자동화
1. **콘텐츠 관리**: 소셜 미디어 포스팅, 블로그 업데이트, 콘텐츠 큐레이션 등
1. **교육 및 연구**: 정보 수집, 문헌 검토, 데이터 분석 등 학술 작업 지원
1. **QA 테스팅**: 웹 애플리케이션의 자동화된 테스트 수행
### **Browser Use를 확장하거나 발전시키기 위한 아이디어**

Browser Use를 더욱 발전시키기 위한 아이디어는 다음과 같습니다:

1. **멀티모달 입력 지원**: 음성, 이미지 등 다양한 입력 방식을 통한 작업 지시
1. **협업 기능**: 여러 AI 에이전트가 협력하여 복잡한 작업을 수행하는 기능
1. **사용자 피드백 학습**: 사용자의 피드백을 통해 에이전트의 성능을 지속적으로 개선
1. **도메인별 특화 에이전트**: 특정 도메인(예: 금융, 의료, 법률 등)에 특화된 에이전트 개발
1. **로컬 모델 지원 강화**: 프라이버시 보호를 위한 로컬 실행 모델 지원 확대
1. **모바일 브라우징 지원**: 모바일 웹사이트 및 앱 자동화 기능 추가
## **결론**

Browser Use의 성공은 AI 기반 웹 자동화 기술의 잠재력을 보여주는 중요한 사례입니다. 이 프로젝트는 복잡한 웹 상호작용을 AI가 이해하고 수행할 수 있는 수준으로 발전시켰으며, 이는 AI 에이전트의 능력이 텍스트 생성을 넘어 실제 세계와의 상호작용으로 확장되고 있음을 보여줍니다.

AgenticReplay와 같은 프로젝트를 구상했던 개발자로서, Browser Use의 성공은 아쉬움과 동시에 이 분야의 발전 가능성에 대한 기대를 갖게 합니다. 특히 웹 요소를 정확하게 식별하고 상호작용하는 기능, 로그인과 같은 복잡한 작업을 처리하는 능력은 매우 인상적입니다.

앞으로 Realtime API와의 통합, 다양한 응용 분야 개척, 기술적 개선 등을 통해 AI 기반 웹 자동화 기술은 더욱 발전할 것으로 기대됩니다. 이러한 발전은 개발자, 비즈니스 사용자, 일반 사용자 모두에게 새로운 가능성을 열어줄 것입니다.

Browser Use와 같은 혁신적인 도구가 등장함에 따라, 우리는 AI가 웹과 상호작용하는 방식의 근본적인 변화를 목격하고 있습니다. 이는 단순한 기술적 발전을 넘어, 인간과 AI의 협업 방식, 웹 서비스 설계 방식, 그리고 궁극적으로는 인터넷을 활용하는 방식 자체를 변화시킬 잠재력을 가지고 있습니다.

