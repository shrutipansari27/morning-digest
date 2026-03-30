#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Morning Digest — One-click GitHub setup script
# Run this once from inside the morning-digest/ folder:
#   bash setup.sh
# ─────────────────────────────────────────────────────────────────
set -e

REPO_NAME="morning-digest"
DESCRIPTION="Daily fintech, investing, MENA & India morning news digest"

echo ""
echo "🌅  Morning Digest — GitHub Setup"
echo "──────────────────────────────────────"

# 1. Check gh CLI is installed
if ! command -v gh &> /dev/null; then
  echo "❌  GitHub CLI (gh) is not installed."
  echo "   Install it from: https://cli.github.com"
  exit 1
fi

# 2. Check logged in
echo "→ Checking GitHub login…"
gh auth status || (echo "❌ Not logged in. Run: gh auth login" && exit 1)

# 3. Create repo
echo "→ Creating GitHub repo '$REPO_NAME'…"
gh repo create "$REPO_NAME" \
  --public \
  --description "$DESCRIPTION" \
  --source=. \
  --remote=origin \
  --push

# 4. Enable GitHub Pages from /docs on main branch
echo "→ Enabling GitHub Pages (docs/ folder)…"
OWNER=$(gh api user --jq '.login')
gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  "/repos/$OWNER/$REPO_NAME/pages" \
  -f source='{"branch":"main","path":"/docs"}' 2>/dev/null || \
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/$OWNER/$REPO_NAME/pages" \
  -f source='{"branch":"main","path":"/docs"}' || true

echo ""
echo "✅  All done!"
echo ""
echo "   🔗 Your digest site:  https://$OWNER.github.io/$REPO_NAME"
echo "   📦 Your repo:         https://github.com/$OWNER/$REPO_NAME"
echo ""
echo "   The site will auto-update every morning at 08:00 UAE time."
echo "   You can also trigger a manual run:"
echo "   → Go to: https://github.com/$OWNER/$REPO_NAME/actions"
echo "   → Click 'Morning Digest — Daily Update' → 'Run workflow'"
echo ""
