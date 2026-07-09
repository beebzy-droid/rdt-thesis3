@echo off
REM Windows shim so `make <target>` works without GNU make (§10.4 portability).
REM Mirrors the Makefile targets; Python is the actual cross-platform entry point.
if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="env" ( pip install -r requirements.txt & goto end )
if "%1"=="gpu" ( pip install -r requirements-gpu.txt & goto end )
if "%1"=="test" ( python -m pytest tests/ -q & goto end )
if "%1"=="screen" ( python scripts/reproduce.py --screen & goto end )
if "%1"=="provenance" ( python scripts/check_provenance.py & goto end )
if "%1"=="figures" ( python scripts/make_figures.py & goto end )
if "%1"=="reproduce" ( python scripts/reproduce.py --all & goto end )
if "%1"=="campaign" (
    python scripts/campaign.py --cats D1,D3,D4,D8 --n 500 --workers 12
    python scripts/campaign_a1_ttr.py --cats D1,D3,D4,D8 --n 500 --workers 12
    python scripts/analysis_prereg.py
    python scripts/analysis_h5_paired.py
    goto end
)
echo Unknown target: %1
:help
echo RDT-Thesis3 targets (Windows): make [env^|gpu^|test^|screen^|provenance^|figures^|reproduce^|campaign]
echo   or run directly: python scripts\reproduce.py
:end
