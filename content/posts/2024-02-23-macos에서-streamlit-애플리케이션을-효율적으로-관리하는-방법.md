---
author: '**Gunn Kim**'
date: '2024-02-23'
description: 이 블로그 포스트에서는 MacOS 환경에서 Streamlit 애플리케이션을 지속적으로 실행하고 관리하는 두 가지 주요 방법을
  소개합니다. nohup을 사용한 백그라운드 실행과 tmux를 활용한 세션 관리 방법을 탐색하며, 실행 상황 모니터링과 프로세스 종료 방법에 대해서도
  논의합니다. 개발자가 자신의 Streamlit 애플리케이션을 더 효과적으로 관리할 수 있도록 도와주는 이 글은 필수 읽을 거리입니다.
draft: false
keywords: &id001
- Tech
- ChatGPT
- Python
lastmod: '2025-04-04T12:26:00.000Z'
notion_id: fd3f3cf4-38a8-4c20-8381-6a5f36f31f47
slug: managing-streamlit-applications-on-macos
subtitle: 지속적인 실행, 모니터링 및 프로세스 관리를 위한 실용적 가이드
summary: 이 블로그 포스트에서는 MacOS 환경에서 Streamlit 애플리케이션을 지속적으로 실행하고 관리하는 두 가지 주요 방법을 소개합니다.
  nohup을 사용한 백그라운드 실행과 tmux를 활용한 세션 관리 방법을 탐색하며, 실행 상황 모니터링과 프로세스 종료 방법에 대해서도 논의합니다.
  개발자가 자신의 Streamlit 애플리케이션을 더 효과적으로 관리할 수 있도록 도와주는 이 글은 필수 읽을 거리입니다.
tags: *id001
title: MacOS에서 Streamlit 애플리케이션을 효율적으로 관리하는 방법
---

집에 있는 맥을 서버로 사용하고 있나요? 맥에서 파이썬 앱을 계속 오픈하고 싶나요? 그러면 이 포스트를 참고하세요. 이 포스트에서는 Streamlit을 이용한 LLM앱을 예시로 들어서 맥에서 파이썬으로 만든 앱이 터미널이 꺼지더라도 실행될 수 있도록 하는 방법을 소개합니다.

# 맥OS에서 Streamlit으로 만든 앱

Streamlit은 데이터 과학자와 개발자가 빠르게 인터랙티브 웹 애플리케이션을 구축할 수 있게 해주는 인기 있는 오픈 소스 도구입니다. 하지만 애플리케이션을 개발하고 테스트하는 과정에서 지속적으로 실행 상태를 유지하고 관리하는 것은 도전적일 수 있습니다. MacOS 사용자를 위해, 우리는 Streamlit 애플리케이션을 효과적으로 실행하고 모니터링하는 데 사용할 수 있는 몇 가지 핵심 전략을 공유하고자 합니다. 이러한 전략은 개발 효율성을 높이고, 프로젝트의 진행 상황을 더 잘 파악할 수 있도록 도와줄 것입니다.

MacOS에서 Streamlit을 지속적으로 실행하기 위한 몇 가지 방법이 있습니다. 여기 가장 일반적인 두 가지 방법을 소개하겠습니다:

### 1. `nohup`을 사용한 백그라운드 실행(쉽고 간편)

`nohup` 명령어는 터미널이 닫혀도 프로세스가 계속 실행되도록 합니다. 이 방법은 간단하고 빠르게 설정할 수 있으며, 로컬 개발이나 테스트에 적합합니다.

1. 터미널을 엽니다.
1. Streamlit 앱을 실행하는 명령어 앞에 `nohup`을 추가하고, `&`을 명령어 끝에 붙여 백그라운드에서 실행하도록 합니다. 예를 들어, `your_app.py`가 Streamlit 앱이라면 다음과 같이 실행합니다:
```plain text
nohup streamlit run your_app.py &

```

1. 이 명령은 `nohup.out` 파일에 앱의 출력을 저장합니다. 앱을 중지하려면 `kill` 명령어와 프로세스 ID를 사용하세요.
### 2. `tmux`를 사용한 세션 관리

`tmux`는 터미널 세션을 관리할 수 있는 도구로, 세션을 분리하고 나중에 다시 연결할 수 있습니다. 이는 개발 과정에서 유용하며, 여러 세션을 동시에 관리할 수 있습니다.

1. `tmux`가 설치되어 있지 않다면, Homebrew를 사용해 설치할 수 있습니다:
```plain text
brew install tmux

```

1. 새 `tmux` 세션을 시작합니다. `streamlit_session`과 같은 이름을 줄 수 있습니다:
```plain text
tmux new -s streamlit_session

```

1. 새로운 `tmux` 세션에서 Streamlit 앱을 실행합니다:
```plain text
streamlit run your_app.py

```

1. 세션을 분리하려면 `Ctrl-B`를 누른 다음 `D`를 누릅니다. 이렇게 하면 `tmux` 세션에서 나오지만, 세션과 Streamlit 앱은 백그라운드에서 계속 실행됩니다.
1. 나중에 다시 연결하려면 다음 명령어를 사용합니다:
```plain text
tmux attach -t streamlit_session

```

이 두 방법은 MacOS에서 Streamlit 애플리케이션을 지속적으로 실행하는 데 유용합니다. 개인적인 필요와 환경에 맞는 방법을 선택하세요.



Streamlit 앱을 `nohup`을 사용해 백그라운드에서 성공적으로 실행한 후, 실행 상황을 모니터링하고 프로세스를 종료하는 방법은 다음과 같습니다:

### 실행 상황 모니터링

- **로그 파일 확인**: `nohup` 명령어는 기본적으로 출력을 `nohup.out` 파일에 저장합니다. 이 파일을 확인하여 앱의 실행 상황을 모니터링할 수 있습니다.
```plain text
tail -f nohup.out

```

`tail -f` 명령어는 파일의 끝부분을 실시간으로 출력해줍니다. 새로운 로그가 기록될 때마다 터미널에 바로 표시됩니다.

- **프로세스 상태 확인**: `ps` 명령어를 사용해 Streamlit 프로세스의 상태를 확인할 수 있습니다. 예를 들어, Streamlit과 관련된 프로세스를 찾으려면 다음과 같이 실행합니다:
```plain text
ps aux | grep streamlit

```

이 명령어는 Streamlit 프로세스의 목록과 상태 정보를 출력합니다.

### 프로세스 종료

- **프로세스 ID를 사용한 종료**: 앞서 `ps aux | grep streamlit` 명령어로 찾은 프로세스 ID(PID)를 사용하여 Streamlit 프로세스를 종료할 수 있습니다.
```plain text
kill -9 PID

```

여기서 `PID`는 종료하려는 프로세스의 식별 번호입니다. `-9` 옵션은 강제 종료를 의미합니다.

- `**pkill**`** 명령어 사용**: `pkill` 명령어를 사용해 프로세스 이름으로 프로세스를 종료할 수도 있습니다. 이 방법은 특정 프로세스 ID를 찾지 않아도 됩니다.
```plain text
pkill -f streamlit

```

- `f` 옵션은 전체 명령어 라인을 대상으로 검색하여 `streamlit`이 포함된 모든 프로세스를 종료합니다.
위 방법을 사용하면 Streamlit 앱의 실행 상황을 모니터링하고 필요할 때 프로세스를 종료할 수 있습니다. 로그 파일을 주기적으로 확인하면 앱의 상태와 발생 가능한 오류를 파악하는 데 도움이 됩니다.

# 나가며: 일반적인 케이스에서는…

<details>
<summary>로컬 터미널에서 Streamlit을 지속적으로 실행하려면 여러 방법이 있습니다. 가장 적합한 방법은 사용 중인 운영 체제와 필요에 따라 다릅니다. 여기 몇 가지 일반적인 접근 방식을 소개합니다:</summary>

1. **nohup을 사용한 백그라운드 실행:**
- `nohup` 명령어를 사용하여 Streamlit 애플리케이션을 백그라운드에서 실행할 수 있습니다. 이 방법은 터미널 세션이 종료되어도 Streamlit이 계속 실행되게 합니다.
- 예시: `nohup streamlit run your_app.py &`
- 이 명령은 `nohup.out` 파일에 로그를 출력합니다.
1. **Screen을 사용한 세션 관리:**
- `screen`은 세션을 분리하고 나중에 다시 연결할 수 있게 해주는 도구입니다. 이를 통해 로컬 컴퓨터에서 Streamlit 애플리케이션을 지속적으로 실행할 수 있습니다.
- `screen` 설치 후, 새 세션을 시작하고 Streamlit 애플리케이션을 실행합니다.
- 예시:
- 세션 시작: `screen -S streamlit`
- Streamlit 실행: `streamlit run your_app.py`
- 세션 분리: `Ctrl-A` 다음 `D`
- 나중에 세션으로 돌아가려면 `screen -r streamlit`을 사용합니다.
1. **tmux를 사용한 세션 관리:**
- `tmux`는 `screen`과 유사한 도구로, 세션 관리 기능을 제공합니다. `tmux`를 사용하면 여러 창과 패널을 사용하여 작업할 수 있습니다.
- `tmux` 세션을 시작하고, Streamlit 애플리케이션을 실행한 다음, 세션에서 분리할 수 있습니다.
- 예시:
- 세션 시작: `tmux new -s streamlit`
- Streamlit 실행: `streamlit run your_app.py`
- 세션 분리: `Ctrl-B` 다음 `D`
- 세션으로 돌아가려면 `tmux attach -t streamlit`을 사용합니다.
1. **시스템 서비스로 설정:**
- Linux 시스템의 경우, Streamlit 애플리케이션을 systemd 서비스로 설정하여 부팅 시 자동으로 시작하게 만들 수 있습니다.
- `/etc/systemd/system/`에 서비스 파일을 만들고, Streamlit 애플리케이션을 실행하는 데 필요한 설정을 정의합니다.
- 서비스를 활성화하여 부팅 시 자동으로 시작하게 설정합니다.
이러한 방법 중 하나를 선택하여 로컬 터미널에서 Streamlit 애플리케이션을 지속적으로 실행할 수 있습니다. 사용 환경과 필요에 따라 가장 적합한 방법을 선택하세요.


</details>

