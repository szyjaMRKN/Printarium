#!/usr/bin/env bash
#
# Buduje paczkę ewidencji gotową do wgrania na hosting współdzielony
# (DirectAdmin + Passenger, np. cyber_Folks).
#
#   ./deploy/cyberfolks/build-package.sh              # aplikacja w /ewidencja
#   ./deploy/cyberfolks/build-package.sh /ksiegowosc  # inny podkatalog
#   ./deploy/cyberfolks/build-package.sh /            # własna domena lub subdomena
#
# Wynik: dist/ewidencja-hosting.zip — zawartość rozpakowuje się wprost
# do katalogu głównego aplikacji Python (Application root) na serwerze.

set -euo pipefail

BASE_PATH="${1:-/ewidencja}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="${REPO_DIR}/dist/hosting"
ZIP_PATH="${REPO_DIR}/dist/ewidencja-hosting.zip"

# Znormalizowana ścieżka bazowa: zawsze z ukośnikiem z przodu, bez z tyłu.
[[ "${BASE_PATH}" == /* ]] || BASE_PATH="/${BASE_PATH}"
BASE_PATH="${BASE_PATH%/}"
[[ -n "${BASE_PATH}" ]] || BASE_PATH="/"

echo "==> Ścieżka aplikacji w domenie: ${BASE_PATH}"

command -v npm >/dev/null || { echo "Brak npm — zainstaluj Node.js 20+." >&2; exit 1; }
command -v python3 >/dev/null || { echo "Brak python3." >&2; exit 1; }

echo "==> Sprawdzam składnię Pythona"
python3 -m compileall -q "${REPO_DIR}/backend/app" "${REPO_DIR}/deploy/cyberfolks/passenger_wsgi.py" >/dev/null

echo "==> Buduję frontend"
cd "${REPO_DIR}/frontend"
if [[ -f package-lock.json ]]; then npm ci --silent; else npm install --silent; fi
VITE_BASE_PATH="${BASE_PATH}" npm run build

echo "==> Składam paczkę"
rm -rf "${BUILD_DIR}" "${ZIP_PATH}"
mkdir -p "${BUILD_DIR}/backend" "${BUILD_DIR}/frontend" "${BUILD_DIR}/data" "${BUILD_DIR}/backups" "${BUILD_DIR}/uploads"

# Backend bez środowiska wirtualnego, testów i cache'u — te rzeczy powstają
# albo są niepotrzebne na serwerze.
cd "${REPO_DIR}/backend"
tar --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' --exclude='tests' \
    --exclude='.pytest_cache' --exclude='htmlcov' --exclude='.coverage' \
    -cf - app alembic alembic.ini requirements.txt | tar -xf - -C "${BUILD_DIR}/backend"

cp -r "${REPO_DIR}/frontend/dist/." "${BUILD_DIR}/frontend/"
cp "${REPO_DIR}/deploy/cyberfolks/passenger_wsgi.py" "${BUILD_DIR}/passenger_wsgi.py"
# Narzędzia obsługiwane z panelu (pole "Wykonaj skrypt Python") — na hostingu
# bez SSH to jedyna droga do diagnostyki i poleceń administracyjnych.
cp "${REPO_DIR}/deploy/cyberfolks/diagnostyka.py" "${BUILD_DIR}/diagnostyka.py"
cp "${REPO_DIR}/deploy/cyberfolks/konsola.py" "${BUILD_DIR}/konsola.py"
# Kopia na wierzchu: panel instaluje zależności z pliku w katalogu aplikacji.
cp "${REPO_DIR}/backend/requirements.txt" "${BUILD_DIR}/requirements.txt"
cp "${REPO_DIR}/deploy/cyberfolks/INSTRUKCJA.txt" "${BUILD_DIR}/INSTRUKCJA.txt"

# Katalogi danych muszą przetrwać spakowanie, a nie mogą być publiczne.
for dir in data backups uploads; do
	printf '%s\n' 'Deny from all' > "${BUILD_DIR}/${dir}/.htaccess"
done

# Wzór konfiguracji z gotowym kluczem i hasłem startowym — na hostingu bez SSH
# nie ma jak uruchomić `openssl rand`. Plik nazywa się `.env.przyklad`, żeby
# ponowne rozpakowanie paczki (aktualizacja) nie nadpisało ustawień na serwerze.
ADMIN_PASSWORD="$(python3 - "${REPO_DIR}/.env.example" "${BUILD_DIR}/.env.przyklad" <<'PYGEN'
import secrets
import string
import sys

wzor, wynik = sys.argv[1], sys.argv[2]

# Wymagania aplikacji: min. 10 znakow, male i wielkie litery oraz cyfra.
alfabet = string.ascii_letters + string.digits
while True:
	haslo = "".join(secrets.choice(alfabet) for _ in range(16))
	if (
		any(z.islower() for z in haslo)
		and any(z.isupper() for z in haslo)
		and any(z.isdigit() for z in haslo)
	):
		break

wartosci = {
	"APP_ENV": "production",
	"SECRET_KEY": secrets.token_urlsafe(48),
	"ENABLE_DOCS": "0",
	"ADMIN_PASSWORD": haslo,
	# Ten sam proces serwuje API i interfejs — na hostingu nie ma osobnego
	# serwera plikow statycznych.
	"FRONTEND_DIR": "frontend",
}
# Ustawienia wylacznie dockerowe — na hostingu wspoldzielonym tylko myla.
zbedne_klucze = ("APP_DOMAIN", "ACME_EMAIL", "APP_UID", "APP_GID")
zbedne_naglowki = (
	"# --- domena i HTTPS (Caddy) ---",
	"# --- użytkownik systemowy dla katalogów danych (id -u / id -g) ---",
)

linie = []
for wiersz in open(wzor, encoding="utf-8").read().splitlines():
	obciety = wiersz.strip()
	if obciety in zbedne_naglowki:
		continue
	klucz = obciety.split("=", 1)[0] if "=" in obciety else ""
	if klucz in zbedne_klucze:
		continue
	if klucz in wartosci:
		wiersz = "%s=%s" % (klucz, wartosci.pop(klucz))
	linie.append(wiersz)

for klucz, wartosc in wartosci.items():
	linie.append("%s=%s" % (klucz, wartosc))

with open(wynik, "w", encoding="utf-8") as plik:
	plik.write("\n".join(linie).replace("\n\n\n", "\n\n") + "\n")

print(haslo)
PYGEN
)"

echo "==> Pakuję"
cd "${BUILD_DIR}"
zip -qr "${ZIP_PATH}" . -x '.DS_Store'
cd "${REPO_DIR}"
rm -rf "${BUILD_DIR}"

echo
echo "Gotowe: ${ZIP_PATH}"
echo "Rozpakuj zawartość w katalogu głównym aplikacji Python na serwerze."
echo "Na serwerze zmień nazwę pliku .env.przyklad na .env."
echo

# W logach CI hasła nie wypisujemy — jest w pliku .env.przyklad w paczce.
if [[ "${PRINT_ADMIN_PASSWORD:-1}" == "1" ]]; then
	echo "Hasło startowe administratora (login: admin): ${ADMIN_PASSWORD}"
	echo "Zapisz je teraz — po pierwszym zalogowaniu zmień hasło w aplikacji."
else
	echo "Hasło startowe administratora znajdziesz w pliku .env.przyklad (ADMIN_PASSWORD)."
fi
