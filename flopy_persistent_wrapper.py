#!/usr/bin/env python3
"""
FloPy Figure Wrapper - Automatically saves matplotlib figures and model files

This wrapper monkey-patches matplotlib and TemporaryDirectory to organize outputs:
- {script_name}/plots/ - All matplotlib figures
- {script_name}/ - All MODFLOW model files

Example structure:
/workspace/
├── dis_voronoi_example.py
└── dis_voronoi_example/
    ├── plots/
    │   ├── figure_001.png
    │   └── ...
    ├── flow/
    │   └── (MODFLOW files)
    └── transport/
        └── (MODFLOW files)

Usage:
    python3 flopy_figure_wrapper.py <script.py>
"""

import sys
import os
from pathlib import Path

# Get script name for output organization
if len(sys.argv) < 2:
    print("Usage: python3 flopy_figure_wrapper.py <script.py>")
    sys.exit(1)

SCRIPT_PATH = sys.argv[1]
SCRIPT_NAME = Path(SCRIPT_PATH).stem  # e.g., "dis_voronoi_example"
OUTPUT_BASE = f'/workspace/{SCRIPT_NAME}'
PLOTS_DIR = f'{OUTPUT_BASE}/plots'
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(OUTPUT_BASE, exist_ok=True)

print(f"Output structure:")
print(f"  Script: {SCRIPT_PATH}")
print(f"  Figures: {PLOTS_DIR}/")
print(f"  Models: {OUTPUT_BASE}/")
print()

# Monkey-patch TemporaryDirectory to use persistent workspace
from tempfile import TemporaryDirectory as OriginalTempDir

class PersistentTempDir:
    """Redirect temporary directories to persistent workspace"""
    def __init__(self, *args, **kwargs):
        self.name = OUTPUT_BASE
        os.makedirs(self.name, exist_ok=True)

    def cleanup(self):
        """Don't delete - keep files for user"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

# Replace TemporaryDirectory
import tempfile
tempfile.TemporaryDirectory = PersistentTempDir

# Set up matplotlib AFTER patching but BEFORE script imports
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution

import matplotlib.pyplot as plt

# Counter for unique figure names
_figure_counter = 0

# Monkey-patch plt.Figure.show to auto-save
_original_show = plt.Figure.show

def auto_save_show(self, *args, **kwargs):
    """Automatically save figure when show() is called"""
    global _figure_counter
    _figure_counter += 1

    # Generate filename from figure number or counter
    fig_num = getattr(self, 'number', _figure_counter)
    filename = os.path.join(PLOTS_DIR, f'figure_{fig_num:03d}.png')

    try:
        self.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"Saved figure to: {filename}")
    except Exception as e:
        print(f"Warning: Failed to save figure {fig_num}: {e}")

    # Call original show (does nothing on Agg backend)
    return _original_show(self, *args, **kwargs)

plt.Figure.show = auto_save_show

# Monkey-patch plt.close to save before closing
_original_close = plt.close

def auto_save_close(fig=None):
    """Save figure before closing"""
    global _figure_counter

    if fig is None:
        # Close all figures
        for num in plt.get_fignums():
            try:
                f = plt.figure(num)
                _figure_counter += 1
                filename = os.path.join(PLOTS_DIR, f'figure_{_figure_counter:03d}_closing.png')
                f.savefig(filename, dpi=150, bbox_inches='tight')
                print(f"Saved closing figure to: {filename}")
            except Exception as e:
                print(f"Warning: Failed to save figure {num}: {e}")
    elif hasattr(fig, 'savefig'):
        # Specific figure object
        _figure_counter += 1
        fig_num = getattr(fig, 'number', _figure_counter)
        filename = os.path.join(PLOTS_DIR, f'figure_{fig_num:03d}_closing.png')
        try:
            fig.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"Saved closing figure to: {filename}")
        except Exception as e:
            print(f"Warning: Failed to save figure: {e}")

    # Call original close
    return _original_close(fig)

plt.close = auto_save_close

# Execute the target script
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 flopy_figure_wrapper.py <script.py>")
        sys.exit(1)

    script_path = sys.argv[1]

    if not os.path.exists(script_path):
        print(f"Error: Script not found: {script_path}")
        sys.exit(1)

    print(f"Running FloPy example with figure auto-save: {script_path}")
    print(f"Figures will be saved to: {PLOTS_DIR}")
    print("-" * 80)

    # Change to script directory for relative imports
    script_dir = os.path.dirname(os.path.abspath(script_path))
    os.chdir(script_dir)

    # Execute the script in global namespace
    with open(script_path, 'r') as f:
        script_code = f.read()

    # Create a globals dict with __name__ set to '__main__'
    script_globals = {
        '__name__': '__main__',
        '__file__': script_path,
    }

    try:
        exec(script_code, script_globals)
    except Exception as e:
        print(f"Error executing script: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Save any remaining open figures
        print("-" * 80)
        print("Finalizing: saving any remaining open figures...")

        for num in plt.get_fignums():
            try:
                fig = plt.figure(num)
                _figure_counter += 1
                filename = os.path.join(PLOTS_DIR, f'figure_{_figure_counter:03d}_final.png')
                fig.savefig(filename, dpi=150, bbox_inches='tight')
                print(f"Saved final figure to: {filename}")
            except Exception as e:
                print(f"Warning: Failed to save final figure {num}: {e}")

        print(f"\nOutput summary:")
        print(f"  Figures: {PLOTS_DIR}/ ({_figure_counter} files)")
        print(f"  Models: {OUTPUT_BASE}/flow/, {OUTPUT_BASE}/transport/")
