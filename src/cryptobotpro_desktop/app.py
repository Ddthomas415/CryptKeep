from __future__ import annotations

def main():
    # Reuse the existing desktop wrapper that starts Streamlit + embedded window
    from packaging.desktop_wrapper import run
    run()

if __name__ == "__main__":
    main()
