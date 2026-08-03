# =============================================================================
# solar-open2 (vLLM 0.22.0 + Solar Open2)
#
# 주의: 이 Makefile은 탭 대신 '>' 를 recipe 구분자로 사용합니다 (.RECIPEPREFIX).
#       복사/붙여넣기로 탭이 공백으로 바뀌어도 깨지지 않습니다.
#       GNU make 3.82 이상 필요 (Ubuntu 24.04 기본 make 4.3 이상이므로 문제 없음).
# =============================================================================

.RECIPEPREFIX := >

IMAGE_REGISTRY ?=
IMAGE_NAME     ?= solar-open2
IMAGE_TAG      ?= dev
IMAGE          := $(if $(IMAGE_REGISTRY),$(IMAGE_REGISTRY)/)$(IMAGE_NAME):$(IMAGE_TAG)

DOCKERFILE ?= Dockerfile
CONTEXT    ?= .
PLATFORM   ?= linux/amd64

# --- 빌드 파라미터 -----------------------------------------------------------
BASE_IMAGE     ?= nvidia/cuda:12.9.1-runtime-ubuntu24.04
UV_IMAGE       ?= ghcr.io/astral-sh/uv:latest
PYTHON_VERSION ?= 3.12
VLLM_REPO      ?= https://github.com/UpstageAI/vllm.git
VLLM_REF       ?= v0.22.0-solar-open2
VLLM_WHEEL     ?= https://github.com/vllm-project/vllm/releases/download/v0.22.0/vllm-0.22.0%2Bcu129-cp38-abi3-manylinux_2_28_x86_64.whl
TORCH_BACKEND  ?= cu129

# --- 로컬 실행 파라미터 ------------------------------------------------------
MODEL_DIR   ?= /mnt/models/Solar-Open2-250B-Nota-INT4-GlobalPruned
SERVED_NAME ?= solar-open2-250b
TP          ?= 2
MAX_LEN     ?= 131072
PORT        ?= 8000

NO_CACHE ?=
PROGRESS ?= auto

BUILD_ARGS := --build-arg BASE_IMAGE=$(BASE_IMAGE) --build-arg UV_IMAGE=$(UV_IMAGE) --build-arg PYTHON_VERSION=$(PYTHON_VERSION) --build-arg VLLM_REPO=$(VLLM_REPO) --build-arg VLLM_REF=$(VLLM_REF) --build-arg VLLM_WHEEL=$(VLLM_WHEEL) --build-arg TORCH_BACKEND=$(TORCH_BACKEND)

.DEFAULT_GOAL := build
.PHONY: patch build push-image release rebuild verify run shell print-image clean help

## patch       : 모델 저장소의 patch/solar_open2.py 를 빌드 컨텍스트로 복사
patch:
> mkdir -p patch
> cp $(MODEL_DIR)/patch/solar_open2.py patch/solar_open2.py
> @ls -l patch/solar_open2.py

## build       : 이미지 빌드 및 태깅
build:
> @test -f patch/solar_open2.py || { echo "ERROR: patch/solar_open2.py 가 없습니다. 'make patch' 를 먼저 실행하십시오."; exit 1; }
> DOCKER_BUILDKIT=1 docker build --platform $(PLATFORM) --progress $(PROGRESS) $(NO_CACHE) -f $(DOCKERFILE) $(BUILD_ARGS) -t $(IMAGE) $(CONTEXT)
> @echo "built: $(IMAGE)"

## push-image  : 레지스트리로 push
push-image:
> docker push $(IMAGE)
> @echo "pushed: $(IMAGE)"

## release     : build 후 push-image
release: build push-image

## rebuild     : 캐시 없이 다시 빌드
rebuild: NO_CACHE := --no-cache
rebuild: build

## verify      : 이미지 안에서 vLLM 버전과 solar_open2 모듈 존재 확인
verify:
> docker run --rm --entrypoint sh $(IMAGE) -c 'D=$$(cat /opt/vllm_pkg_dir); echo "vllm dir: $$D"; python -c "import importlib.metadata as m; print(\"vllm version:\", m.version(\"vllm\"))"; ls -l "$$D/model_executor/models/solar_open2.py" "$$D/v1/sample/logits_processor/solar_open2.py" "$$D/reasoning/solar_open2_reasoning_parser.py" "$$D/tool_parsers/solar_open2_tool_parser.py"; if cmp -s "$$D/model_executor/models/solar_open2.py" "$$D/model_executor/models/solar_open2.py.orig"; then echo "PATCH: NOT applied"; else echo "PATCH: applied"; fi; if command -v cc >/dev/null; then echo "CC: $$(cc -dumpversion)"; else echo "CC: MISSING"; fi; if [ -x /usr/local/cuda/bin/nvcc ]; then echo "NVCC: $$(/usr/local/cuda/bin/nvcc --version | grep release)"; else echo "NVCC: MISSING"; fi'

## run         : 로컬에서 GPU로 서빙 테스트
run:
> docker run --rm -it --gpus all --ipc=host -p $(PORT):8000 -v $(MODEL_DIR):$(MODEL_DIR):ro $(IMAGE) serve $(MODEL_DIR) --served-model-name $(SERVED_NAME) --tensor-parallel-size $(TP) --trust-remote-code --max-model-len $(MAX_LEN) --default-chat-template-kwargs '{"think_render_option":"preserved"}' --reasoning-parser solar_open2 --tool-call-parser solar_open2 --enable-auto-tool-choice --logits-processors vllm.v1.sample.logits_processor.solar_open2:SolarOpen2TemplateLogitsProcessor

## shell       : 컨테이너 셸 진입
shell:
> docker run --rm -it --entrypoint bash $(IMAGE)

## print-image : 최종 이미지 이름 출력
print-image:
> @echo $(IMAGE)

## clean       : 로컬 이미지 삭제
clean:
> -docker rmi $(IMAGE)

## help        : 타깃 목록
help:
> @grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## //'
