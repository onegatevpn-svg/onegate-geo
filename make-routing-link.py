#!/usr/bin/env python3
"""
Превращает routing-profile.json в ссылку happ://routing/add/<base64>
и печатает готовый SQL для панели 3x-ui.

    python3 make-routing-link.py

Опции:
    --repo    другой GitHub-репозиторий, если сменится владелец или имя.
    --onadd   собрать happ://routing/onadd/... — принудительная активация
              профиля, даже если у пользователя активен другой.
              Нужно ровно один раз, при первой раскатке нового профиля;
              дальше достаточно обычного add.
"""
import argparse
import base64
import json
import time

ap = argparse.ArgumentParser()
ap.add_argument("--repo", default="Route1/onegate-geo",
                help="GitHub-репозиторий в виде владелец/имя")
ap.add_argument("--profile", default="routing-profile.json")
ap.add_argument("--onadd", action="store_true")
args = ap.parse_args()

raw = open(args.profile, encoding="utf-8").read()
raw = raw.replace("__TS__", str(int(time.time())))
profile = json.loads(raw)  # заодно проверка, что JSON валиден

# адреса баз всегда пересобираются из --repo, чтобы они не разъехались
base = f"https://cdn.jsdelivr.net/gh/{args.repo}@release"
profile["geositeurl"] = f"{base}/geosite.dat"
profile["geoipurl"] = f"{base}/geoip.dat"

# компактно, без пробелов — ссылка и так длинная
blob = json.dumps(profile, ensure_ascii=False, separators=(",", ":")).encode()
b64 = base64.b64encode(blob).decode()

verb = "onadd" if args.onadd else "add"
link = f"happ://routing/{verb}/{b64}"

print(f"имя профиля : {profile['name']}")
print(f"geosite     : {profile['geositeurl']}")
print(f"geoip       : {profile['geoipurl']}")
print(f"длина ссылки: {len(link)} символов\n")

print("── ссылка ──")
print(link)
print()
print("── что выполнить на сервере подписки ──")
sql_value = link.replace("'", "''")
print("systemctl stop x-ui && sleep 2")
print("sqlite3 /etc/x-ui/x-ui.db \"UPDATE settings SET value='"
      + sql_value + "' WHERE key='subRoutingRules';\"")
print("sqlite3 /etc/x-ui/x-ui.db \"UPDATE settings SET value='true' "
      "WHERE key='subEnableRouting';\"")
print("rm -f /etc/x-ui/x-ui.db-wal /etc/x-ui/x-ui.db-shm")
print("systemctl start x-ui")
