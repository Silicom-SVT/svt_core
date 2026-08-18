# svt_core

Shared primitives for the [SVT ecosystem](https://github.com/Silicom-SVT).

Extracted from `svt_framework` so that both `svt_framework` and `svt_modules`
can depend on these building blocks without creating a circular dependency.

## What's included

| Module | Contents |
|---|---|
| `svt_core.stats` | `Stats` dataclass — tracks pass/fail counts per cycle |
| `svt_core.config` | `load_config` — TOML config loader |
| `svt_core.logger` | `Logger`, `ExcelLog`, `LogLevel` — logging infrastructure |
| `svt_core.ssh` | `SSHClient`, `SSHTimeoutError` — SSH communication |

## Installation

```bash
pip install git+https://github.com/Silicom-SVT/svt_core.git
```

## Dependency graph

```
svt_core  ←── svt_modules
svt_core  ←── svt_framework
              svt_framework ←── svt_modules
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
