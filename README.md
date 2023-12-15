# Server

## Run Celery Workers
`BASE_DIR`: 프로젝트 디렉터리

```bash
cd BASE_DIR && pipenv shell
celery -A recommender.tasks worker -n scrape@%h -Q scrape -l INFO --logfile=/home/myungjune/projects/maifit-server/scraper-worker.log
```

```bash
cd BASE_DIR && conda activate MultiPerson
celery -A recommender.tasks worker -n estimate@%h -Q estimate -l INFO --logfile=/home/myungjune/projects/maifit-server/estimate-worker.log
```

## Pipenv 설치
pipenv를 설치하려면 다음 명령을 실행합니다:

`pip install pipenv`

## 파이썬 3.10.3 가상환경 만들기
파이썬 버전 3.10.3으로 새 가상 환경을 생성: 

`pipenv --python 3.10.3`

Python 버전 3.10.3이 설치되어 있지 않은 경우 conda를 통해 설치 가능:

`conda install python=3.10.3`

## Pipenv 기본 사용법
새 가상 환경을 만들고 Pipfile.lock에 명시된 의존성 설치:

`pipenv install`

가상 환경 활성화:

`pipenv shell`

가상 환경 비활성화:

`exit`

## .env 파일 만들기
프로젝트의 루트 디렉터리에 아래 내용으로 .env 파일 생성:

```
SECRET_KEY=<아무거나>
```

## 패키지 설치하기
패키지를 설치하려면 `pip install` 대신:

`pipenv install <package-name>`

`pipenv install`은 패키지를 설치하고 Pipfile에 추가하는 명령어입니다. 

`git push` 전에 Pipfile.lock에 새 패키지를 포함시켜야 합니다. 다음 명령어를 실행한 다음 push하세요. 

`pipenv lock`

## VS Code 세팅

1. Ctrl+Shift+P(Windows/Linux) 또는 Cmd+Shift+P(macOS)를 눌러 명령 팔레트를 엽니다.
2. `Python: Select Interpreter`
3. 목록에서 가상 환경의 인터프리터를 선택합니다.

### 가상 환경 찾기
목록에 가상 환경이 안 뜨기도 합니다. 

`pipenv --venv`로 가상 환경 경로를 찾을 수 있습니다. 