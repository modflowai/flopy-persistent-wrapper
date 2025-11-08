# FloPy Persistent Wrapper

Automatically saves matplotlib figures and MODFLOW model files from FloPy examples without modifying original scripts.

Makes temporary directories and figures persistent in organized workspace structure.

## Usage

```bash
python3 flopy_persistent_wrapper.py <script.py>
```

## Output Structure

```
/workspace/{script_name}/
├── plots/                  # All matplotlib figures
│   ├── figure_001.png
│   ├── figure_002.png
│   └── ...
└── (all model files)       # MODFLOW input/output files
```

## How It Works

- Monkey-patches `matplotlib.pyplot` to auto-save all figures
- Monkey-patches `tempfile.TemporaryDirectory` to use persistent workspace
- Organizes all outputs in clean directory structure
