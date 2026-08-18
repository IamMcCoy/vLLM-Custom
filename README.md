# vLLM-Custom

커스텀 vLLM 서빙 이미지 모음 저장소입니다. 모델(또는 vLLM 포크)별로 디렉터리를 나누어 Dockerfile과 빌드 도구를 관리합니다.

## 프로젝트 목록

| 디렉터리 | 설명 |
|---|---|
| [`solar-open2/`](solar-open2/) | vLLM 0.22.0 (UpstageAI Solar Open2 브랜치) 기반 Solar Open2 250B 서빙 이미지. Global-Pruned 패치 포함. |
| [`hyperclovax/`](hyperclovax/) | vLLM v0.20.0 (공식 `vllm/vllm-openai` 이미지) 기반 HyperCLOVAX-SEED-Think-32B 서빙 이미지. μP/Peri-LN 모델 + `hcx` reasoning/tool 파서 플러그인 포함. |

## 공통 구조

각 프로젝트 디렉터리는 다음을 포함합니다.

- `Dockerfile` — 서빙 이미지 빌드 정의
- `Makefile` — 빌드 / 검증 / 로컬 실행 / 레지스트리 push 타깃
- `README.md` — 해당 프로젝트의 상세 사용법
- (선택) `plugin/` 등 이미지에 들어가는 커스텀 소스

push 대상 레지스트리는 `IMAGE_REGISTRY` 변수로 지정합니다. 자세한 사용법은 각 프로젝트의 README를 참고하십시오.

## 새 프로젝트 추가

1. 가장 비슷한 프로젝트 디렉터리를 복사합니다 (공식 이미지 + 플러그인이면 `hyperclovax/`, 소스 빌드 + 패치면 `solar-open2/`).
2. `Makefile` 상단의 `IMAGE_NAME`, `# --- 빌드 파라미터 ---`, `# --- 로컬 실행 파라미터 ---` 블록과 `run` 타깃의 서빙 플래그만 수정합니다. 타깃 이름(`build/verify/run/push-image/release/...`)은 그대로 둡니다.
3. `Dockerfile` 에 커스텀 소스(`plugin/`) 반영과 검증 단계를 넣고, `README.md` 는 같은 섹션 순서(빠른 시작 → Make 타깃 → 주요 변수 → 서빙 옵션 → 빌드 동작 요약 → 참고)로 작성합니다.
4. 위 프로젝트 목록 표에 한 줄 추가합니다.
