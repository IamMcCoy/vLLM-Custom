# syntax=docker/dockerfile:1.7
#
# vLLM 0.22.0 (UpstageAI Solar Open2 브랜치) 서빙 이미지

ARG BASE_IMAGE=nvidia/cuda:12.9.1-runtime-ubuntu24.04
ARG UV_IMAGE=ghcr.io/astral-sh/uv:latest

FROM ${UV_IMAGE} AS uvbin

FROM ${BASE_IMAGE}

ARG PYTHON_VERSION=3.12
ARG VLLM_REPO=https://github.com/UpstageAI/vllm.git
ARG VLLM_REF=v0.22.0-solar-open2
ARG VLLM_WHEEL=https://github.com/vllm-project/vllm/releases/download/v0.22.0/vllm-0.22.0%2Bcu129-cp38-abi3-manylinux_2_28_x86_64.whl
ARG TORCH_BACKEND=cu129
ARG VLLM_VERSION=0.22.0

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:/usr/local/bin:${PATH} \
    UV_LINK_MODE=copy \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python

# 1) 기본 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uvbin /uv /usr/local/bin/uv

# 2) venv 생성
RUN uv venv --python ${PYTHON_VERSION} /opt/venv

# 3) vLLM 설치 (소스: Solar Open2 브랜치 / 커널: 공식 v0.22.0 wheel)
RUN \
    VLLM_USE_PRECOMPILED=1 \
    VLLM_PRECOMPILED_WHEEL_LOCATION="${VLLM_WHEEL}" \
    VLLM_VERSION_OVERRIDE="${VLLM_VERSION}" \
    SETUPTOOLS_SCM_PRETEND_VERSION="${VLLM_VERSION}" \
    uv pip install \
        --no-cache \
        --python /opt/venv/bin/python \
        --reinstall-package vllm \
        --torch-backend=${TORCH_BACKEND} \
        "git+${VLLM_REPO}@${VLLM_REF}"

# 4) 설치 경로 해석 + solar_open2 모듈 검증
RUN set -eux; \
    VLLM_PKG_DIR="$(/opt/venv/bin/python -c 'import importlib.util, os; print(os.path.dirname(importlib.util.find_spec("vllm").origin))')"; \
    echo "${VLLM_PKG_DIR}" > /opt/vllm_pkg_dir; \
    echo "resolved vllm package dir = ${VLLM_PKG_DIR}"; \
    /opt/venv/bin/python -c 'import importlib.metadata as m; print("vllm version =", m.version("vllm"))'; \
    for f in \
        model_executor/models/solar_open2.py \
        v1/sample/logits_processor/solar_open2.py \
        reasoning/solar_open2_reasoning_parser.py \
        tool_parsers/solar_open2_tool_parser.py ; do \
        if [ -f "${VLLM_PKG_DIR}/${f}" ]; then \
            echo "OK      ${f}"; \
        else \
            echo "MISSING ${f}"; exit 1; \
        fi; \
    done

# 5) Global-Pruned 패치 적용 (레이어별 expert 수 지원)
COPY patch/solar_open2.py /tmp/patch/solar_open2.py

RUN set -eux; \
    VLLM_PKG_DIR="$(cat /opt/vllm_pkg_dir)"; \
    TARGET="${VLLM_PKG_DIR}/model_executor/models/solar_open2.py"; \
    cp "${TARGET}" "${TARGET}.orig"; \
    cp /tmp/patch/solar_open2.py "${TARGET}"; \
    /opt/venv/bin/python -m py_compile "${TARGET}"; \
    if cmp -s "${TARGET}" "${TARGET}.orig"; then \
        echo "WARNING: patch is identical to upstream file"; \
    else \
        echo "patch applied: ${TARGET}"; \
    fi; \
    rm -rf /tmp/patch

# 6) 런타임 컴파일 도구 (Triton: gcc / FlashInfer: nvcc)
RUN apt-get update && apt-get install -y --allow-change-held-packages --no-install-recommends \
        build-essential \
        cuda-nvcc-12-9 \
        cuda-cudart-dev-12-9 \
        libcurand-12-9 libcurand-dev-12-9 \
        libcublas-12-9 libcublas-dev-12-9 \
    && rm -rf /var/lib/apt/lists/*

ENV CC=gcc \
    CXX=g++ \
    CUDA_HOME=/usr/local/cuda \
    PATH=/usr/local/cuda/bin:${PATH}

RUN set -eux; \
    /usr/local/cuda/bin/nvcc --version; \
    cc --version; \
    test -f /usr/local/cuda/include/curand.h; \
    test -f /usr/local/cuda/include/cublas_v2.h; \
    echo "cuda headers OK"

# 7) 런타임
WORKDIR /workspace
EXPOSE 8000

# k8s Deployment args 예시 (TP는 짝수 2 또는 4만 가능):
#   serve /mnt/models/Solar-Open2-250B-Nota-INT4-GlobalPruned
#   --served-model-name=solar-open2-250b --tensor-parallel-size=2
#   --trust-remote-code --max-model-len=131072
#   --reasoning-parser=solar_open2 --tool-call-parser=solar_open2
#   --enable-auto-tool-choice
#   --logits-processors=vllm.v1.sample.logits_processor.solar_open2:SolarOpen2TemplateLogitsProcessor
ENTRYPOINT ["vllm"]
CMD ["serve", "--help"]
