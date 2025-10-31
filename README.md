# PickleChecker 🔍

A security analysis tool for scanning Python pickle files and ML models for potential security threats. It integrates multiple scanning engines to detect malicious code, unsafe imports, and suspicious patterns in pickle files and model weights.

## Features

- 🔍 Multi-engine scanning
- 📁 Support for directory, file, and HuggingFace model scanning  
- 🎯 Detection of unsafe imports and malicious code patterns

### Supported Scanners
- [Fickling](https://github.com/trailofbits/fickling)
- [Picklescan](https://github.com/mmaitre314/picklescan)
- [Modelscan](https://github.com/protectai/modelscan)

## Installation

```bash
# Clone the repository
git clone https://github.com/Prehistoic/PickleChecker.git
cd picklechecker

# Install dependencies
pip install -r requirements.txt
```

> [!IMPORTANT]
> Make sure to copy `.env.template` to `.env` and update `HF_TOKEN` with an Access Token generated from [HuggingFace](https://huggingface.co/settings/tokens)

## Usage

```bash
# Scan a single file
python picklechecker.py --file path/to/pickle.pkl

# Scan a directory
python picklechecker.py --directory path/to/model/dir

# Scan a HuggingFace model
python picklechecker.py --model "organization/model-name"

# Enable verbose output
python picklechecker.py -v --file path/to/pickle.pkl
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License 📃

This project is under BSD-3-Clause License. See [LICENSE](./LICENSE.md) for more details.