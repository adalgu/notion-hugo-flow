---
author: Gunn Kim
date: '2025-03-16T19:09:00.000Z'
draft: true
keywords: &id001
- Uncategorized
lastmod: '2025-03-16T19:09:00.000Z'
notion_id: 1b87522e-eb2f-8167-9f67-e805f8e0d931
tags: *id001
title: '[node.js] 안드로이드폰을 node.js 서버로 만들기'
---

1. 안드로이드폰에 termux를 설치한다.
1. 먼저, `apt-get update` 실행
1. 이어서, Node.js 설치
```javascript
업데이트 진행
$ apt update && apt upgrade

coreutils 설치
$ apt install coreutils

vim 설치
$ apt install vim

nodejs 설치
$ apt install nodejs

프로젝트 폴더 만들기(예: /myserver/)
mkdir myserver
cd myserver

package.json 파일 생성
$ npm init
```


1. Express 모듈 설치
1. 코드를 적을 index.js 파일 생성
1. 서버 실행
1. 서버 접속
1. 외부 IP로 접속해 보자


1. Ngrok 백그라운드로 실행
1. Node.js 실행
1. 브라우저로 접속
