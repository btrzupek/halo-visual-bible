#!/usr/bin/env bash
# One-time setup for reader reports (api/report.js):
#   1. creates the private repo btrzupek/halo-visual-bible-reports and its labels
#   2. opens GitHub's new fine-grained token page, prefilled (you pick the repo and click Generate)
#   3. checks the token you paste can file issues there and nowhere else it shouldn't
#   4. stores it in Vercel as REPORTS_TOKEN (Production and Preview)
#   5. optionally redeploys a preview and sends one real test report
#
#   bash scripts/setup_reports.sh [preview-url]
#
# Safe to rerun: existing repo and labels are kept, the Vercel variable is replaced.
# The token is read silently and only ever passed on stdin; it is not echoed or saved to disk.
set -euo pipefail

OWNER=btrzupek
REPO=halo-visual-bible-reports
SCOPE=btrzupeks-projects
PROJECT=halo-visual-bible
PREVIEW=${1:-}
cd "$(dirname "$0")/.."

# gh as btrzupek without switching the active account (same trick as the push command in CLAUDE.md)
export GH_TOKEN; GH_TOKEN=$(gh auth token -u "$OWNER")

echo "== 1. Private repo $OWNER/$REPO"
if gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  echo "   exists, keeping it"
else
  gh repo create "$OWNER/$REPO" --private --disable-wiki \
    --description "Reader reports from the Visual Bible site (filed by /api/report)"
fi
lbl() { gh label create "$1" --repo "$OWNER/$REPO" --color "$2" --description "$3" --force >/dev/null; }
lbl reader-report d4b066 "Filed from the site's Report a problem dialog"
lbl image 8a6a2c "The scene's picture"
lbl audio 5d6072 "The scene's narration"
for b in genesis 1samuel 2samuel 1kings 2kings 1chronicles 2chronicles matthew mark luke john acts; do
  lbl "book:$b" cfc3a9 "$b"
done
echo "   labels ready"

echo
echo "== 2. Fine-grained token"
URL="https://github.com/settings/personal-access-tokens/new?name=halo-visual-bible-reports&description=Vercel+%2Fapi%2Freport+files+reader+reports&target_name=$OWNER&expires_in=366&issues=write"
echo "   Opening: $URL"
echo "   On that page:"
echo "     - Repository access: 'Only select repositories' -> $OWNER/$REPO (only that one)"
echo "     - Permissions: Issues = Read and write (prefilled); Metadata = Read (automatic). Nothing else."
echo "     - Generate token and copy it."
open "$URL" 2>/dev/null || true
echo
read -r -s -p "   Paste the token (input hidden), then Enter: " TOKEN; echo
[ -n "$TOKEN" ] || { echo "   no token given"; exit 1; }

echo
echo "== 3. Checking the token"
api() { curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" "https://api.github.com$1"; }
code=$(api "/repos/$OWNER/$REPO/issues?per_page=1")
[ "$code" = 200 ] || { echo "   token cannot read issues on $OWNER/$REPO (HTTP $code). Check its repository access."; exit 1; }
echo "   can read issues on $OWNER/$REPO"
code=$(api "/repos/$OWNER/halo-visual-bible/issues?per_page=1")
if [ "$code" = 200 ]; then
  echo "   WARNING: it can also see $OWNER/halo-visual-bible. It only needs the reports repo;"
  echo "   consider regenerating it with 'Only select repositories'."
else
  echo "   cannot see the site repo (good)"
fi

echo
echo "== 4. Vercel: REPORTS_TOKEN for Production and Preview"
[ -f .vercel/project.json ] || vercel link --yes --project "$PROJECT" --scope "$SCOPE" >/dev/null
for env in production preview; do vercel env rm REPORTS_TOKEN "$env" --yes >/dev/null 2>&1 || true; done
# no git-branch argument: applies to every Preview branch
printf '%s' "$TOKEN" | vercel env add REPORTS_TOKEN production,preview --sensitive >/dev/null
echo "   set for production and preview"
unset TOKEN
vercel env ls 2>/dev/null | grep REPORTS_TOKEN || echo "   (could not list; check Project > Settings > Environment Variables)"

if [ -z "$PREVIEW" ]; then
  echo
  echo "Done. Env vars apply to new deployments only: redeploy (or push) before testing."
  echo "To redeploy a preview and send a test report: bash scripts/setup_reports.sh <preview-url>"
  exit 0
fi

echo
echo "== 5. Redeploying $PREVIEW and sending a test report"
NEW=$(vercel redeploy "$PREVIEW" --scope "$SCOPE" 2>/dev/null | grep -Eo 'https://[a-z0-9.-]+\.vercel\.app' | tail -1)
[ -n "$NEW" ] || { echo "   redeploy did not return a URL; redeploy from the dashboard and test by hand"; exit 1; }
echo "   new preview: $NEW"
BODY='{"t":9000,"slug":"mark","chapter":3,"verse":1,"last":6,"kind":"image","reason":"other","file":"halo_edit_00079_.png","note":"Setup test from scripts/setup_reports.sh. Close me.","url":"'"$NEW"'/mark#s3-1"}'
vercel curl "$NEW/api/report" -s -X POST -H "Origin: $NEW" -H 'Content-Type: application/json' -d "$BODY" 2>/dev/null | grep -E '^\{' || true
sleep 3
echo "   newest issues in $OWNER/$REPO:"
gh issue list --repo "$OWNER/$REPO" --limit 3
