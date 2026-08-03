# vLLM-Custom

커스텀 vLLM 서빙 이미지 모음 저장소입니다. 모델(또는 vLLM 포크)별로 디렉터리를 나누어 Dockerfile과 빌드 도구를 관리합니다.

## 프로젝트 목록

| 디렉터리 | 설명 |
|---|---|
| [`solar-open2/`](solar-open2/) | vLLM 0.22.0 (UpstageAI Solar Open2 브랜치) 기반 Solar Open2 250B 서빙 이미지. Global-Pruned 패치 포함. |

## 공통 구조

각 프로젝트 디렉터리는 다음을 포함합니다.

- `Dockerfile` — 서빙 이미지 빌드 정의
- `Makefile` — 빌드 / 검증 / 로컬 실행 / 레지스트리 push 타깃
- `README.md` — 해당 프로젝트의 상세 사용법

push 대상 레지스트리는 `IMAGE_REGISTRY` 변수로 지정합니다. 자세한 사용법은 각 프로젝트의 README를 참고하십시오.
