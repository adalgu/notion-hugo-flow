---
author: Gunn Kim
date: '2025-03-16T19:09:00.000Z'
draft: true
lastmod: '2025-03-16T19:09:00.000Z'
notion_id: 1b87522e-eb2f-81f1-9f55-e2554ed74d29
title: '[Notion] 노션에 구글 애드센스 달기(feat. 능력자분들의 조언을 구합니다.)'
---


- 원래는 불가능하지만, 트릭을 쓰면 가능하다
- 현재 페이지, [oopy.gunn.kim](https://oopy.gunn.kim/)(아래 그림 왼쪽)으로 접속하면 하단에 배너가 뜨는 것을 볼 수 있다.

## 우피에서 구글 애드센스가 가능하다는 점은 두가지 힌트를 암시한다.


힌트 1) 이미 허가받은 구글 애드센스 계정과 해당 도메인을 활용한다. (노션 페이지만으로 웹사이트를 만들고 심사를 받는 것은 가능은 할테지만, 통과가 쉽지는 않을듯)

ㄴ 이미 구글 애드센스를 허가받은 도메인의 하위 네임을 이용하면 상대적으로 쉬울 것으로 보인다. 예를 들어, [https://gunn.kim](https://gunn.kim/) 으로 허가받은 애드센스가 있다면, https://oopy.gunn.kim에 무리없이 애드센스를 달 수 있다는 것을 확인할 수 있다.


힌트 2) Cloudflare Workers를 이용하여 웹사이트 부를 때 애드센스 코드를 불러서 노션 페이지에 레이어로 올려준다.

ㄴ 일부 능력자들이 이미 시도한 것을 볼 수 있는데, 우피가 아마도 유사한 방식을 채택한 것으로 생각된다.

[https://www.facebook.com/groups/notion.so/permalink/1040808083047842/](https://www.facebook.com/groups/notion.so/permalink/1040808083047842/)



## 결론적으로, 

노션에 구글 애드센스를 달 수 있다. 다만, 개인 도메인을 보유하고 있고, 이를 이용해서 애드센스 고시를 통과한 상태에서 설치가 용이한 점을 확인할 수 있다.


그렇다면, 우피를 이용하지 않고, 개인 도메인만으로 노션에 애드센스를 달 수 있는 방법은 무엇인가?

위 페이스북 캡쳐에 있듯이, Cloudflare의 Workers와 App을 이용해야 한다. 즉, 클라우드플레어 워커스를 이용해서 노션 웹페이지 로딩할때 구글애드센스 스크립트를 로딩하도록 하는 것.

1. Cloudflare workers에 애드센스 스크립트를 삽입한다.
1. Cloudflare App을 이용하여 ads.txt 추가한다.(Quick을 이용하는 방식)
### 여기까지 다 수행한 상황이나 아직 목표한 [https://notion.gunn.kim](https://notion.gunn.kim/) 에 뜨지 않는 상황이다.


### 해결책은?

1) 위에까지 하고, 아래 코드를 노션 페이지에서 불러오도록 만들면 해결될 것으로 보이는데, 아직 완전히 문제를 해소하지는 못하고 있다. (Help me!)

```html
<!-- notion-ad -->
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-369509860207****"
     data-ad-slot="**********"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({});
</script>
```


2) Workers Example을 참고해서, body에 위 코드를 fetch하면 되지 않을까?라고 생각 중이다.

구글 애드센스 스크립트를 cloudflare workers에서 불러오는 것이 방법이긴 할 것 같은데, 조금 더 공부가 필요한 상황이다.

> Fetch HTML
Send a request to a remote server, read HTML from the response, and serve that HTML.

```javascript

/**
 * Example someHost at url is set up to respond with HTML
 * Replace url with the host you wish to send requests to
 */
const someHost = "https://examples.cloudflareworkers.com/demos"
/**  const url = someHost + "/static/html" */

const url = `
<!doctype html>
<html lang="en">
<body>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-369509860207****"
     crossorigin="anonymous"></script>
<!-- 사각형 디스플레이 -->
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-369509860207****"
     data-ad-slot="301574****"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({});
</script>
</body>
</html>
`

/**
 * gatherResponse awaits and returns a response body as a string.
 * Use await gatherResponse(..) in an async function to get the response body
 * @param {Response} response
 */
async function gatherResponse(response) {
  const { headers } = response
  const contentType = headers.get("content-type") || ""
  if (contentType.includes("application/json")) {
    return JSON.stringify(await response.json())
  }
  else if (contentType.includes("application/text")) {
    return response.text()
  }
  else if (contentType.includes("text/html")) {
    return response.text()
  }
  else {
    return response.text()
  }
}

async function handleRequest() {
  const init = {
    headers: {
      "content-type": "text/html;charset=UTF-8",
    },
  }
  const response = await fetch(url, init)
  const results = await gatherResponse(response)
  return new Response(results, init)
}

addEventListener("fetch", event => {
  return event.respondWith(handleRequest())
})
```


완전히 작동할 때까지 가즈아~!! 끝.



[[Notion] 노션과 도메인 연결하기](https://www.notion.so/736f0e70d77e447a9cb9a7b85b984c96) 

[[Notion] 노션 페이지에 구글 애널리틱스(GA) 넣기](https://www.notion.so/98f036d8186942f78a3b0b1e5293b306) 

[[Notion] 노션에 방문자 카운트 삽입](https://www.notion.so/30f7001845844848b437c6784a1b5b7e) 



