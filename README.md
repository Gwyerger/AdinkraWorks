# AdinkraWorks

> A specialized visualization tool for exploring Adinkras for supersymmetry research

[![Version](https://img.shields.io/badge/version-1.0-blue.svg)](https://github.com/Gwyerger/AdinkraWorks.git)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-brightgreen.svg)](https://www.python.org/)

## Overview

**AdinkraWorks** is an interactive viewer and library management system for Adinkra diagrams—graphical representations used in the study of supersymmetric representations. Built with Python and Qt, AdinkraWorks provides researchers with an intuitive interface for organizing, visualizing, and exporting Adinkras.

## Features

✨ **Library Management**
- Create hierarchical libraries organized into Theories and individual Adinkras
- Support for multiple concurrent library instances
- Best suited for Python and Mathematica workflows 
- Exporting capabilities

🎨 **Interactive Visualization**
- Click-and-drag node manipulation
- Smooth panning and zooming (Ctrl/Cmd + scroll)
- Customizable appearance: edge thickness, colors, node size, and label styling

📸 **Export Options**
- Save Adinkras as images or vector graphics
- Choose between screen view or full diagram export
- High-quality output for publications and presentations

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/Gwyerger/AdinkraWorks.git
cd AdinkraWorks

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/__main__.py
```

### Quick Start Guide

1. **Import an Adinkra**: Currently, AdinkraWorks supports importing pre-defined Adinkras (see [Writing Adinkras](#writing-adinkras) below)
2. **Create a Library**: Organize your Adinkras into Theories within a Library structure
3. **Visualize**: Interact with your diagrams using click-and-drag, pan, and zoom controls
4. **Customize**: Access `Preferences` to adjust visual settings
5. **Export**: Save your work via `File > Export As`

## Writing Adinkras

### From Python

Use the `Adinkra.py` module to convert your Adinkra representations to CSV format:

```python
from Adinkra import Adinkra_to_CSV

# Your Adinkra matrices
Ls = [NDArray...]  # L matrices
Rs = [NDArray...]  # R matrices

# Export to CSV
Adinkra_to_CSV("/path/to/output.csv", Ls, Rs)
```

For source code, see the `Adinkra.py` module.

### From Mathematica

Export your Adinkra matrices using the following syntax:

```mathematica
Export["/path/to/My_Adinkra_Matrices.csv", {{{Ls, Rs}}}, "CSV"]
```

## Controls Reference

| Action | Control |
|--------|---------|
| Move nodes | Click and drag nodes |
| Pan view | Click and drag white space |
| Zoom | `Ctrl`/`Cmd` + mouse wheel |

## Roadmap

- [ ] Native Adinkra creation from scratch
- [ ] Native Adinkra creation from NCube Quotienting
- [ ] Advanced Visualization tools

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For questions, bug reports, or feature requests, please contact:

📧 **gabeyerger@gmail.com**

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Special thanks to the supersymmetry research community for their continued support and feedback.

---

*Developed with ❤️ for physics research | Last updated: October 2025*