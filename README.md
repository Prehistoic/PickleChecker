# PickleChecker 🔍

A security analysis tool for scanning Python pickle files and ML models for potential security threats. It integrates multiple scanning engines to detect malicious code, unsafe imports, and suspicious patterns in pickle files and model weights.

## Features ✨

- 🔍 Multi-engine scanning
- 📁 Support for directory, file, and HuggingFace model scanning
- 🎯 Detection of unsafe imports and malicious code patterns
- 🔧 Support for adding your own whitelisted/blacklisted global imports
- 📄 Export scan results to PDF reports

## Installation 🖥️

```bash
# Clone the repository
git clone https://github.com/Prehistoic/PickleChecker.git
cd picklechecker

# Install picklechecker
pip install .
```

> [!IMPORTANT]
> Make sure to copy `.env.template` to `.env` and update `HF_TOKEN` with an Access Token generated from [HuggingFace](https://huggingface.co/settings/tokens) if you wish to scan gatekept models.

## Usage 🚀

```bash
# Scan a single file
picklechecker --file path/to/pickle.pkl

# Scan a directory
picklechecker --directory path/to/model/dir

# Scan a HuggingFace model
picklechecker --model "organization/model-name"

# Enable verbose output
picklechecker -v --file path/to/pickle.pkl

# Export to PDF
picklechecker --file path/to/pickle.pkl --output result.pdf --format pdf

# Add safe globals (module:name or JSON file)
picklechecker --file path/to/pickle.pkl --add-safe os:path --add-safe /path/to/safe.json

# Add unsafe globals
picklechecker --directory /path --add-unsafe subprocess:call
```

## Contributing 🚧

Contributions are welcome! Please feel free to submit a Pull Request.

## License 📃

This project is under BSD-3-Clause License. See [LICENSE](./LICENSE.md) for more details.