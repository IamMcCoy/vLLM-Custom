# solar-open2

vLLM 0.22.0 기반 **Solar Open2 250B** 서빙 이미지입니다.

- 소스: [UpstageAI/vllm](https://github.com/UpstageAI/vllm) `v0.22.0-solar-open2` 브랜치
- 커널: 공식 vLLM `v0.22.0` precompiled wheel (cu129) 재사용 → 소스 컴파일 없이 빠른 빌드
- 패치: `plugin/solar_open2.py` — Global-Pruned 모델 지원 (레이어별 expert 수 상이)
- 베이스: `nvidia/cuda:12.9.1-runtime-ubuntu24.04` + Python 3.12 (uv venv)
- 런타임 컴파일 도구 포함: gcc (Triton), nvcc 12.9 (FlashInfer)

## 빠른 시작

```bash
# 1) 모델 저장소에서 패치 파일 복사 (최초 1회 또는 패치 갱신 시)
make patch

# 2) 이미지 빌드
make build

# 3) 이미지 내부 검증 (vLLM 버전, solar_open2 모듈, 패치 적용 여부, gcc/nvcc)
make verify

# 4) 로컬 GPU 서빙 테스트
make run

# 5) 레지스트리 push (build + push는 make release)
make push-image
```

기본 이미지 태그: `solar-open2:dev` (`IMAGE_REGISTRY` 지정 시 `<registry>/solar-open2:dev`)

## Make 타깃

`make help`로도 확인할 수 있습니다.

| 타깃 | 설명 |
|---|---|
| `patch` | `$(MODEL_DIR)/patch/solar_open2.py` 를 빌드 컨텍스트(`plugin/`)로 복사 |
| `build` | 이미지 빌드 (기본 타깃, `plugin/solar_open2.py` 없으면 실패) |
| `rebuild` | `--no-cache` 로 다시 빌드 |
| `verify` | 이미지 안에서 vLLM 버전 / 모듈 / 패치 / 컴파일러 확인 |
| `run` | 로컬 GPU에서 서빙 테스트 (`--gpus all`, 포트 8000) |
| `shell` | 컨테이너 bash 진입 |
| `push-image` | 레지스트리로 push |
| `release` | build + push-image |
| `print-image` | 최종 이미지 이름 출력 |
| `clean` | 로컬 이미지 삭제 |

## 주요 변수 (덮어쓰기 가능)

```bash
make build IMAGE_TAG=v0.22.0-r1
make run TP=4 PORT=8080
```

| 변수 | 기본값 | 설명 |
|---|---|---|
| `IMAGE_REGISTRY` | (없음) | 레지스트리 (push 시 지정 필요) |
| `IMAGE_TAG` | `dev` | 이미지 태그 |
| `MODEL_DIR` | `/mnt/models/Solar-Open2-250B-Nota-INT4-GlobalPruned` | 모델 경로 (patch/run에서 사용) |
| `SERVED_NAME` | `solar-open2-250b` | `--served-model-name` |
| `TP` | `2` | tensor parallel size (**짝수 2 또는 4만 가능**) |
| `MAX_LEN` | `131072` | `--max-model-len` |
| `PORT` | `8000` | 호스트 포트 |
| `VLLM_REF` | `v0.22.0-solar-open2` | 빌드할 vLLM git ref |

## 서빙 옵션 (k8s Deployment args 예시)

이미지 ENTRYPOINT는 `vllm`이므로 args에 `serve ...`를 넘깁니다.

```
serve /mnt/models/Solar-Open2-250B-Nota-INT4-GlobalPruned
--served-model-name=solar-open2-250b
--tensor-parallel-size=2
--trust-remote-code
--max-model-len=131072
--reasoning-parser=solar_open2
--tool-call-parser=solar_open2
--enable-auto-tool-choice
--logits-processors=vllm.v1.sample.logits_processor.solar_open2:SolarOpen2TemplateLogitsProcessor
```

`make run`은 여기에 `--default-chat-template-kwargs '{"think_render_option":"preserved"}'` 를 추가로 사용합니다.

## 빌드 동작 요약 (Dockerfile)

1. uv로 Python 3.12 venv 생성 (`/opt/venv`)
2. `VLLM_USE_PRECOMPILED=1` 로 Solar Open2 브랜치 소스를 설치하되, 컴파일 커널은 공식 v0.22.0 wheel에서 가져옴
3. `solar_open2` 관련 4개 모듈(model / logits_processor / reasoning parser / tool parser) 존재 검증 — 없으면 빌드 실패
4. `plugin/solar_open2.py` 로 모델 코드 교체 (원본은 `.orig`로 백업, `py_compile`로 문법 검증)
5. Triton/FlashInfer 런타임 JIT 컴파일용 gcc + nvcc 12.9 설치

## 참고

- Makefile은 탭 대신 `>` 를 recipe 구분자로 사용합니다 (`.RECIPEPREFIX`). GNU make 3.82 이상 필요.
- `make patch`는 모델 디렉터리가 마운트된 환경에서만 동작합니다. 복사된 `plugin/solar_open2.py`는 git으로 관리됩니다.
