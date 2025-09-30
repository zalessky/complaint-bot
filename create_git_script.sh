#!/bin/bash
cat > push_to_github.sh << 'SCRIPTEOF'
#!/bin/bash
set -e
echo "🚀 Выгрузка v0.8.2"
echo ""
BRANCH=$(git branch --show-current 2>/dev/null || echo "master")
[ -z "$BRANCH" ] && BRANCH="master"
echo "Ветка: $BRANCH"
echo ""
git status --short
echo ""
read -p "Продолжить? (y/n) " -n 1 -r
echo
[[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
git add .
git commit -m "Release v0.8.2"
git tag v0.8.2
git push origin $BRANCH
git push --tags
echo ""
echo "✅ Готово!"
git remote get-url origin
SCRIPTEOF
chmod +x push_to_github.sh
echo "✅ Скрипт создан: push_to_github.sh"
