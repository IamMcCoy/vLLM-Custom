# syntax=docker/dockerfile:1.7
#
# vLLM v0.20.0 (공식 vllm-openai 이미지) + HyperCLOVAX 플러그인 서빙 이미지
# vllm docker: https://hub.docker.com/r/vllm/vllm-openai/tags

ARG VLLM_VERSION=v0.20.0
FROM vllm/vllm-openai:${VLLM_VERSION}

ENV VLLM_WORKER_MULTIPROC_METHOD=spawn
WORKDIR /workspace

# 1) 플러그인 설치 (모델 / reasoning 파서 / tool 파서 → vllm.general_plugins 로 자동 등록)
#    챗 템플릿은 자동 주입되지 않으므로 기동 시 --chat-template 로 지정
COPY plugin /workspace/HyperCLOVAX
RUN pip install --no-cache-dir -e /workspace/HyperCLOVAX/

# 2) 플러그인 검증 — 엔트리포인트를 실제로 로드해 모델/파서 등록 확인 (CPU에서 동작)
RUN python3 -c 'from vllm.plugins import load_general_plugins; load_general_plugins(); \
    from vllm import ModelRegistry; from vllm.reasoning import ReasoningParserManager; from vllm.tool_parsers import ToolParserManager; \
    assert "HyperCLOVAXForCausalLM" in ModelRegistry.get_supported_archs(); \
    ReasoningParserManager.get_reasoning_parser("hcx"); ToolParserManager.get_tool_parser("hcx"); print("plugin OK")' \
    && test -f /workspace/HyperCLOVAX/chat_template_hcx.jinja

# 3) 런타임
EXPOSE 8000

# k8s Deployment args 예시
#   (기동 전 EOS 100273 반영: python3 /workspace/HyperCLOVAX/patch_generation_config.py <model-dir>)
#   --model /mnt/models/HyperCLOVAX-SEED-Think-32B
#   --served-model-name HyperCLOVAX-SEED-Think-32B
#   --tensor-parallel-size 2 --max-model-len 32768 --max-num-seqs 8
#   --reasoning-parser hcx --tool-call-parser hcx --enable-auto-tool-choice
#   --disable-custom-all-reduce
#   --chat-template /workspace/HyperCLOVAX/chat_template_hcx.jinja
ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server"]
