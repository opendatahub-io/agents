# Local vLLM on Apple Silicon

This is a basic script to test vLLM on apple silicon with tool calling. This will not work for gpt-OSS.

https://docs.vllm.ai/en/latest/getting_started/installation/cpu.html

## Requirements

- uv
- python
- git

## Installation

This script will clone vllm, build it from source for macos, then deploy it in CPU only mode with a basic opensource tool parser, the deepseek r1 reasoning parser, and QWEN 3 0.6b as the main model.

```sh
./vllm-mac.sh
```
