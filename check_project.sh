#!/bin/bash
set -e

echo "🟢 Starting full project check..."

# Step 1: Project structure
echo -e "\n📂 Checking project structure..."
required_dirs=(scripts services storage docs)
for d in "${required_dirs[@]}"; do
  if [ ! -d "$d" ]; then
    echo "❌ Missing directory: $d"
  else
    echo "✅ Found directory: $d"
  fi
done

# Step 2: Key files
echo -e "\n📄 Checking key files..."
files=(Dockerfile docker-compose.yml requirements.txt)
for f in "${files[@]}"; do
  if [ ! -f "$f" ]; then
    echo "❌ Missing file: $f"
  else
    echo "✅ Found file: $f (size: $(stat -f%z "$f") bytes)"
  fi
done

# Step 3: Phase docs
echo -e "\n📄 Checking phase docs (only existing ones)..."
for doc in docs/PHASE*_*.md; do
  if [ -f "$doc" ]; then
    echo "✅ Found doc: $doc"
  fi
done

# Step 4: Python
echo -e "\n🐍 Checking Python..."
if command -v python3 >/dev/null 2>&1; then
  echo "✅ Python3 found: $(python3 --version)"
else
  echo "❌ Python3 not installed"
  exit 1
fi

# Step 5: Python import check
export PYTHONPATH=.
echo -e "\n🔧 Testing script import..."
if python3 -c "from services.runtime.process_supervisor import start_process, status" 2>/dev/null; then
  echo "✅ Python imports working"
else
  echo "❌ Python imports failed, check PYTHONPATH or missing files"
fi

# Step 6: Docker
echo -e "\n🐳 Checking Docker..."
if ! command -v docker >/dev/null 2>&1; then
  echo "❌ Docker not installed"
else
  echo "✅ Docker installed: $(docker --version)"
fi

echo "Checking Docker daemon..."
if docker info >/dev/null 2>&1; then
  echo "✅ Docker daemon running"
else
  echo "❌ Docker daemon not running"
fi

# Step 7: Scripts
echo -e "\n📜 Checking scripts..."
for s in scripts/*.py; do
  if [ -f "$s" ] && [ -s "$s" ]; then
    echo "✅ Script OK: $s"
  else
    echo "❌ Script missing or empty: $s"
  fi
done

# Step 8: Docker Compose syntax
echo -e "\n🚀 Testing Docker Compose build..."
if [ -f docker-compose.yml ]; then
  if docker compose config >/dev/null 2>&1; then
    echo "✅ docker-compose.yml syntax OK"
  else
    echo "❌ docker-compose.yml invalid"
  fi
else
  echo "❌ docker-compose.yml missing"
fi

echo -e "\n✅ Full check complete!"

