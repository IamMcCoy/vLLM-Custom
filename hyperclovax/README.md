# hyperclovax

vLLM v0.20.0 기반 **HyperCLOVAX-SEED-Think-32B** 서빙 이미지입니다.

- 베이스: 공식 [`vllm/vllm-openai:v0.20.0`](https://hub.docker.com/r/vllm/vllm-openai/tags) 이미지
- 플러그인: `plugin/` — HyperCLOVAX 모델(μP / Peri-LN) + `hcx` reasoning/tool 파서를 `vllm.general_plugins` 엔트리포인트로 등록
- 챗 템플릿: `plugin/chat_template_hcx.jinja` (이미지 안 `/workspace/HyperCLOVAX/chat_template_hcx.jinja`)

> **지원 모델:** **HyperCLOVAX-SEED-Think-32B 전용.** 14B는 tool calling을 신뢰성 있게
> 수행하지 못해(추론 후 `<tool_call>` 미출력, temperature 0에서도 재현) **미지원**.
>
> **기준 버전:** vLLM **v0.20.0** (`--reasoning-parser` / `--tool-call-parser` 인터페이스 및
> `vllm.tool_parsers`, `vllm.entrypoints.openai.engine.protocol` 경로 기준). 그 이하 버전은 모듈 경로가 달라 동작하지 않을 수 있다.

## 빠른 시작

```bash
# 1) 모델 generation_config.json 에 EOS 100273 추가 (최초 1회, 멱등)
make patch-eos

# 2) 이미지 빌드
make build

# 3) 이미지 내부 검증 (vLLM 버전, 모델/파서 실제 등록, 챗 템플릿)
make verify

# 4) 로컬 GPU 서빙 테스트
make run

# 5) 레지스트리 push (build + push는 make release)
make push-image
```

기본 이미지 태그: `hyperclovax:dev` (`IMAGE_REGISTRY` 지정 시 `<registry>/hyperclovax:dev`)

## Make 타깃

`make help`로도 확인할 수 있습니다.

| 타깃 | 설명 |
|---|---|
| `patch-eos` | `$(MODEL_DIR)/generation_config.json` 에 EOS `100273` 추가 (멱등, 호스트 python) |
| `build` | 이미지 빌드 (기본 타깃) |
| `rebuild` | `--no-cache` 로 다시 빌드 |
| `verify` | 이미지 안에서 vLLM 버전 / 모델·파서 실제 등록 / 챗 템플릿 확인 |
| `run` | 로컬 GPU에서 서빙 테스트 (`--gpus all`, 포트 8000) |
| `shell` | 컨테이너 bash 진입 |
| `push-image` | 레지스트리로 push |
| `release` | build + push-image |
| `print-image` | 최종 이미지 이름 출력 |
| `clean` | 로컬 이미지 삭제 |

## 주요 변수 (덮어쓰기 가능)

```bash
make build IMAGE_TAG=v0.20.0-r1
make run TP=4 PORT=8080
```

| 변수 | 기본값 | 설명 |
|---|---|---|
| `IMAGE_REGISTRY` | (없음) | 레지스트리 (push 시 지정 필요) |
| `IMAGE_TAG` | `dev` | 이미지 태그 |
| `VLLM_VERSION` | `v0.20.0` | 베이스 `vllm/vllm-openai` 태그 |
| `MODEL_DIR` | `/mnt/models/HyperCLOVAX-SEED-Think-32B` | 모델 경로 (patch-eos/run에서 사용) |
| `SERVED_NAME` | `HyperCLOVAX-SEED-Think-32B` | `--served-model-name` |
| `TP` | `2` | tensor parallel size |
| `MAX_LEN` | `32768` | `--max-model-len` |
| `MAX_NUM_SEQS` | `8` | `--max-num-seqs` |
| `PORT` | `8000` | 호스트 포트 |

## 서빙 옵션 (k8s Deployment args 예시)

이미지 ENTRYPOINT는 `python3 -m vllm.entrypoints.openai.api_server`이므로 args에 플래그만 넘깁니다.

```
--model /mnt/models/HyperCLOVAX-SEED-Think-32B
--served-model-name HyperCLOVAX-SEED-Think-32B
--host 0.0.0.0
--port 8000
--gpu-memory-utilization 0.9
--tensor-parallel-size 2
--max-model-len 32768
--max-num-seqs 8
--reasoning-parser hcx
--enable-auto-tool-choice
--tool-call-parser hcx
--disable-custom-all-reduce
--chat-template /workspace/HyperCLOVAX/chat_template_hcx.jinja
```

`--reasoning-parser hcx`를 함께 켜면 `<think>` 추론부는 reasoning 파서가 처리하고,
추론이 끝난 뒤에야 tool 파서가 호출된다(중복 처리 없음).

> **EOS 토큰(`100273` 추가):** 모델의 `generation_config.json`을 직접 패치해야 한다
> (`--override-generation-config` 플래그는 적용되지 않음). 이미지에 포함된
> `/workspace/HyperCLOVAX/patch_generation_config.py` 가 멱등 패치 스크립트다.
> 모델 마운트가 RW면 vLLM 기동 **전에** 실행하고(아래 예시), RO 마운트면 `make patch-eos` 등으로
> 모델 빌드 단계에서 미리 반영한다.

```yaml
command: ["sh", "-c"]
args:
  - |
    python3 /workspace/HyperCLOVAX/patch_generation_config.py /mnt/models/HyperCLOVAX-SEED-Think-32B
    exec python3 -m vllm.entrypoints.openai.api_server \
      --model /mnt/models/HyperCLOVAX-SEED-Think-32B \
      --served-model-name HyperCLOVAX-SEED-Think-32B \
      --host 0.0.0.0 --port 8000 \
      --gpu-memory-utilization 0.9 --tensor-parallel-size 2 \
      --max-model-len 32768 --max-num-seqs 8 \
      --reasoning-parser hcx --enable-auto-tool-choice --tool-call-parser hcx \
      --disable-custom-all-reduce \
      --chat-template /workspace/HyperCLOVAX/chat_template_hcx.jinja
```

## 빌드 동작 요약 (Dockerfile)

1. `vllm/vllm-openai:${VLLM_VERSION}` 베이스 (`VLLM_WORKER_MULTIPROC_METHOD=spawn`)
2. `plugin/` 을 `/workspace/HyperCLOVAX` 로 복사 후 `pip install -e` — 모델/파서가 `vllm.general_plugins` 로 자동 등록
3. 플러그인을 실제 로드해 `HyperCLOVAXForCausalLM` / `hcx` reasoning 파서 / `hcx` tool 파서 등록과 챗 템플릿 존재 검증 — 실패 시 빌드 중단

## 플러그인 상세 (`plugin/`)

HyperCLOVAX(HCX) 모델을 vLLM에서 서빙하기 위한 플러그인. LLaMA 구조에 아래 변경을 적용한다.
- [μP](https://arxiv.org/pdf/2203.03466)
- [Peri-LN](https://arxiv.org/pdf/2502.02732)

### 구성 요소

| 구성 | 파일 | 등록 이름 |
|------|------|-----------|
| 모델 | [plugin/model/vllm_hyperclovax.py](plugin/model/vllm_hyperclovax.py) | `HyperCLOVAXForCausalLM` |
| Reasoning 파서 | [plugin/parser/hcx_reasoner.py](plugin/parser/hcx_reasoner.py) | `hcx` |
| Tool 파서 | [plugin/parser/hcx_tool_parser.py](plugin/parser/hcx_tool_parser.py) | `hcx` |
| 챗 템플릿 | [plugin/chat_template_hcx.jinja](plugin/chat_template_hcx.jinja) | — |
| EOS 패치 스크립트 | [plugin/patch_generation_config.py](plugin/patch_generation_config.py) | — |

`plugin/setup.py`의 `vllm.general_plugins` 엔트리포인트로 모델/파서가 자동 등록된다.
**챗 템플릿은 자동 주입되지 않으므로** 기동 시 `--chat-template`로 지정해야 한다.

### 모델 설정 (μP / Peri-LN)

[plugin/model/configuration_hyperclovax.py](plugin/model/configuration_hyperclovax.py)

- μP
  - **embedding_multiplier** (`float`, default `None`) — 임베딩 가중치 배수. `None`이면 `1.0`.
  - **logits_scaling** (`float`, default `None`) — 로짓 스케일. `None`이면 `1.0`.
  - **attention_multiplier** (`float`, default `None`) — 어텐션 가중치 배수. `None`이면 `self.head_dim ** -0.5`.
  - **residual_multiplier** (`float`, default `None`) — 잔차 연결 스케일. `None`이면 `1.0`.
- Peri-LN
  - **use_post_norm** (`bool`, default `False`) — Peri-Layer Normalization 적용 여부. `True`로 활성화.

### 챗 템플릿

[plugin/chat_template_hcx.jinja](plugin/chat_template_hcx.jinja) (32B 기준).

- thinking 분기: `{%- if enable_thinking is not defined or enable_thinking is true %}`.
- `enable_thinking` **미지정 시 thinking ON**(`<think>` 생성). `hcx_reasoner.py` 폴백 기본값도 ON으로 맞춰져 있다.
- 명시적으로 끄려면 `chat_template_kwargs={"enable_thinking": false}`를 보낸다.

### Tool calling

모델은 챗 템플릿이 지시한 아래 XML 포맷으로 함수 호출을 출력한다.

```
<tool_call>get_weather
<arg_key>city</arg_key>
<arg_value>서울</arg_value>
</tool_call>
```

[plugin/parser/hcx_tool_parser.py](plugin/parser/hcx_tool_parser.py)가 이 포맷을 OpenAI 호환
`tool_calls`로 변환한다. `<arg_value>`는 문자열이면 원문, 그 외(숫자/불리언/객체)는
JSON으로 들어오므로 `json.loads` 시도 후 실패하면 문자열로 복원한다. 문자열 인자
하나만 담는 `<arguments>{json}</arguments>` 형태도 지원한다.

### 이미지 없이 설치 (git clone 방식)

공식 `vllm/vllm-openai` 이미지에서 이 저장소를 클론해 직접 설치할 수도 있다.
`pip install -e`로 설치하면 챗 템플릿도 클론 디렉터리에 함께 들어오므로 `--chat-template`에
클론 경로를 그대로 지정한다.

```bash
git clone https://github.com/IamMcCoy/vLLM-Custom.git /tmp/vllm-custom
pip install -e /tmp/vllm-custom/hyperclovax/plugin
python3 -m vllm.entrypoints.openai.api_server ... \
    --chat-template /tmp/vllm-custom/hyperclovax/plugin/chat_template_hcx.jinja
```

## 참고

- Makefile은 탭 대신 `>` 를 recipe 구분자로 사용합니다 (`.RECIPEPREFIX`). GNU make 3.82 이상 필요.
- 플러그인 원본: NAVER Cloud HyperCLOVAX vLLM plugin 을 커스텀한 것 (구 `hcx-vllm-plugin-custom` 저장소를 subtree로 편입, 커밋 히스토리 보존).
- 라이선스: Apache-2.0 — [LICENSE](LICENSE), [NOTICE](NOTICE) (Copyright (c) 2025-present NAVER Cloud Corp.)
