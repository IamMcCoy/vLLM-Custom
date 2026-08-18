# =============================================================================
# hyperclovax (vLLM v0.20.0 + HyperCLOVAX 플러그인)
#
# 주의: 이 Makefile은 탭 대신 '>' 를 recipe 구분자로 사용합니다 (.RECIPEPREFIX).
#       복사/붙여넣기로 탭이 공백으로 바뀌어도 깨지지 않습니다.
#       GNU make 3.82 이상 필요.
# =============================================================================

.RECIPEPREFIX := >

IMAGE_REGISTRY ?=
IMAGE_NAME     ?= hyperclovax
IMAGE_TAG      ?= dev
IMAGE          := $(if $(IMAGE_REGISTRY),$(IMAGE_REGISTRY)/)$(IMAGE_NAME):$(IMAGE_TAG)

DOCKERFILE ?= Dockerfile
CONTEXT    ?= .
PLATFORM   ?= linux/amd64

# --- 빌드 파라미터 -----------------------------------------------------------
VLLM_VERSION ?= v0.20.0

# --- 로컬 실행 파라미터 ------------------------------------------------------
MODEL_DIR    ?= /mnt/models/HyperCLOVAX-SEED-Think-32B
SERVED_NAME  ?= HyperCLOVAX-SEED-Think-32B
TP           ?= 2
MAX_LEN      ?= 32768
MAX_NUM_SEQS ?= 8
PORT         ?= 8000
CHAT_TEMPLATE := /workspace/HyperCLOVAX/chat_template_hcx.jinja

NO_CACHE ?=
PROGRESS ?= auto

BUILD_ARGS := --build-arg VLLM_VERSION=$(VLLM_VERSION)

.DEFAULT_GOAL := build
.PHONY: patch-eos build push-image release rebuild verify run shell print-image clean help

## patch-eos   : $(MODEL_DIR)/generation_config.json 에 EOS 100273 추가 (멱등, 호스트 python 사용)
patch-eos:
> python3 plugin/patch_generation_config.py $(MODEL_DIR)

## build       : 이미지 빌드 및 태깅
build:
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

## verify      : 이미지 안에서 vLLM 버전과 플러그인 실제 등록(모델/reasoning 파서/tool 파서) 확인
verify:
> docker run --rm --entrypoint python3 $(IMAGE) -c 'import importlib.metadata as m; print("vllm version:", m.version("vllm")); from vllm.plugins import load_general_plugins; load_general_plugins(); from vllm import ModelRegistry; from vllm.reasoning import ReasoningParserManager; from vllm.tool_parsers import ToolParserManager; assert "HyperCLOVAXForCausalLM" in ModelRegistry.get_supported_archs(), "model not registered"; print("model: HyperCLOVAXForCausalLM"); print("reasoning parser:", ReasoningParserManager.get_reasoning_parser("hcx").__name__); print("tool parser:", ToolParserManager.get_tool_parser("hcx").__name__); import os; assert os.path.isfile("$(CHAT_TEMPLATE)"), "chat template missing"; print("chat template: $(CHAT_TEMPLATE)")'

## run         : 로컬에서 GPU로 서빙 테스트
run:
> docker run --rm -it --gpus all --ipc=host -p $(PORT):8000 -v $(MODEL_DIR):$(MODEL_DIR):ro $(IMAGE) --model $(MODEL_DIR) --served-model-name $(SERVED_NAME) --tensor-parallel-size $(TP) --max-model-len $(MAX_LEN) --max-num-seqs $(MAX_NUM_SEQS) --gpu-memory-utilization 0.9 --reasoning-parser hcx --enable-auto-tool-choice --tool-call-parser hcx --disable-custom-all-reduce --chat-template $(CHAT_TEMPLATE)

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
