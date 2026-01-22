# Desktop Build Notes

- Uses pywebview to wrap Streamlit in a native window.
- PyInstaller builds: one folder, not cross-compiled (build Windows on Windows, macOS on macOS).
- Safe defaults enforced; kill switch active.
- Run the built binary to start Streamlit locally and open native window.
