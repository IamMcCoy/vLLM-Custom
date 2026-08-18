#!/usr/bin/env python3
"""모델 generation_config.json 에 EOS 토큰 100273 을 추가한다 (멱등).

`--override-generation-config` 플래그로는 반영되지 않으므로 vLLM 기동 전에 실행한다.
RO 마운트면 실패하므로 모델 빌드 단계에서 미리 반영할 것.

사용: python3 patch_generation_config.py <model-dir>
"""
import json
import pathlib
import sys

HCX_EOS_TOKEN_ID = 100273


def patch(model_dir: str) -> bool:
    """추가했으면 True, 이미 있으면 False."""
    p = pathlib.Path(model_dir) / "generation_config.json"
    c = json.loads(p.read_text())
    e = c.get("eos_token_id")
    e = e if isinstance(e, list) else [e]
    if HCX_EOS_TOKEN_ID in e:
        return False
    c["eos_token_id"] = e + [HCX_EOS_TOKEN_ID]
    p.write_text(json.dumps(c, ensure_ascii=False, indent=2))
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    changed = patch(sys.argv[1])
    print(f"generation_config.json: EOS {HCX_EOS_TOKEN_ID} {'added' if changed else 'already present'}")
