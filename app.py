#!/usr/bin/env python3
import sys
from pathlib import Path

# Add src to Python path for direct Streamlit execution
root_dir = Path(__file__).resolve().parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from trafficvision.ui.app import main  # noqa: E402

if __name__ == "__main__":
    main()
else:
    # When executed via streamlit run app.py
    main()
