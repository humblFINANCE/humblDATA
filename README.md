<p align="center">
  <img src="./docs/assets/temp_humbldata_logo.png" alt="Project logo" width="200px">
</p>

<h3 align="center">humbldata</h3>

<div align="center">

  [![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/jjfantini/humbldata)
  [![Open in GitHub Codespaces](https://img.shields.io/static/v1?label=GitHub%20Codespaces&message=Open&color=blue&logo=github)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=450509735)
  [![Status](https://img.shields.io/badge/status-active-success.svg)]()
  [![GitHub Issues](https://img.shields.io/github/issues/jjfantini/humbldata.svg)](https://github.com/jjfantini/humbldata/issues)
  [![GitHub Pull Requests](https://img.shields.io/github/issues-pr/jjfantini/humbldata.svg)](https://github.com/jjfantini/humbldata/pulls)

  [![Python](https://img.shields.io/badge/Python-3.11.7-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
  [![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
  [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
  [![Commitizen friendly](https://img.shields.io/badge/commitizen-friendly-brighgreen.svg)](http://commitizen.github.io/cz-cli/)
  <a href="https://gitmoji.dev"><img src="https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg" alt="Gitmoji"></a>
  <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-lightgreen?logo=pre-commit" alt="pre-commit"></a>
  <a href="https://github.com/semantic-release/semantic-release"><img src="https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg" alt="semantic-release"></a>


  ![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-black)

</div>

---
`humbldata` connects the humblfinance web app to its data sources and in-house analysis. A thin wrapper around the most popular open-source financial data providers, with some extra flair to use the same tools and math as the big guys. how do i know? because i used to pay a pretty penny for it! no longer... OSS is here to save the day!

# 🌟 Main Features 🌟
- **Mandelbrot Channel**
  - price channel of <span style="color:green"><b>BUY</b></span> / <span style="color:red"><b>SELL</b></span> levels used by the largest quant firms
  - this is a popular indicator used to provide robust price boundaries for any asset, but no one has **open-sourced** it until now...
- **Realized Volatility Estimators**
  - all volatility calculations in Euan Sinclar's book, plus 2 extra.
  - ⚡ lightning fast estimators use Rust under the hood

# Getting Started

Insall with `pip:`
```bash
pip install humbldata
```
Install with `poetry`
```bash
poetry add humbldata
```

## Documentation

To understand the structure of this **codebase**, the **commands** available and how to **contribute**, please refer to the [documentation](https://humblfinance.github.io/humbldata/)

