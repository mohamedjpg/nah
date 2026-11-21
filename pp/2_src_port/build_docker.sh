#!/usr/bin/env bash
# Linux/macOS build helper — runs in a VS2022 Docker container.
#   docker run -v "$PWD":/src -w /src mcr.microsoft.com/windows/servercore:ltsc2022
#   (VS2022 BuildTools image is heavier; ltsc2022 has cl/link/rc on PATH.)

set -euo pipefail
cd "$(dirname "$0")"

# If cl.exe is not already on PATH, try common VS2022 locations
if ! command -v cl.exe >/dev/null 2>&1; then
    for d in \
        "C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build" \
        "C:/Program Files/Microsoft Visual Studio/2022/Professional/VC/Auxiliary/Build" \
        "C:/Program Files/Microsoft Visual Studio/2022/Enterprise/VC/Auxiliary/Build" \
        "C:/Program Files/Microsoft Visual Studio/2022/BuildTools/VC/Auxiliary/Build"; do
        if [[ -f "$d/vcvars64.bat" ]]; then
            source "$d/vcvars64.bat"
            break
        fi
    done
fi

# Verify the toolchain
cl.exe 2>&1 | head -2
link.exe 2>&1 | head -1
rc.exe /? 2>&1 | head -1

# Build order: port first, then AIO
cmd.exe /c build_port.bat
cmd.exe /c build_aio.bat

echo "=== BUILD OK ==="
ls -la ../1_run/RobRunPort.exe ../1_run/RobRunAIO.exe 2>/dev/null || true