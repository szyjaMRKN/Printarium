#!/usr/bin/env bash
#
# Buduje paczkę ZIP motywu Printarium, gotową do wgrania w panelu WordPressa.
#
# Użycie:
#   ./build.sh            – buduje dist/printarium.zip
#   ./build.sh 1.1.0      – najpierw podbija wersję w style.css, potem buduje
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEME="printarium"
SRC="$ROOT/$THEME"
DIST="$ROOT/dist"

if [ ! -d "$SRC" ]; then
	echo "Nie znaleziono katalogu motywu: $SRC" >&2
	exit 1
fi

# --- Opcjonalne podbicie wersji -------------------------------------------
if [ $# -ge 1 ]; then
	NEW_VERSION="$1"
	sed -i.bak -E "s/^Version: .*/Version: ${NEW_VERSION}/" "$SRC/style.css"
	sed -i.bak -E "s/define\( 'PRINTARIUM_VERSION', '[^']*' \)/define( 'PRINTARIUM_VERSION', '${NEW_VERSION}' )/" "$SRC/functions.php"
	rm -f "$SRC/style.css.bak" "$SRC/functions.php.bak"
	echo "Ustawiono wersję: ${NEW_VERSION}"
fi

VERSION="$(grep -m1 '^Version:' "$SRC/style.css" | sed -E 's/Version:[[:space:]]*//')"

# --- Weryfikacja składni PHP ----------------------------------------------
if command -v php >/dev/null 2>&1; then
	echo "Sprawdzam składnię PHP…"
	ERRORS=0
	while IFS= read -r file; do
		if ! php -l "$file" >/dev/null 2>&1; then
			php -l "$file" || true
			ERRORS=1
		fi
	done < <(find "$SRC" -name '*.php')

	if [ "$ERRORS" -ne 0 ]; then
		echo "Przerwano – wykryto błędy składni." >&2
		exit 1
	fi
	echo "Składnia PHP: OK"
else
	echo "PHP niedostępne – pomijam weryfikację składni."
fi

# --- Pakowanie -------------------------------------------------------------
rm -rf "$DIST"
mkdir -p "$DIST"

cd "$ROOT"
zip -r -q "$DIST/${THEME}.zip" "$THEME" \
	-x "*/.git/*" "*/.DS_Store" "*/node_modules/*" "*/.gitkeep" "*.bak"

SIZE="$(du -h "$DIST/${THEME}.zip" | cut -f1)"

echo
echo "Gotowe: dist/${THEME}.zip  (wersja ${VERSION}, ${SIZE})"
echo "Wgraj przez: Wygląd → Motywy → Dodaj nowy → Wyślij motyw na serwer"
