#!/usr/bin/env python3
"""
Превращает routing-profile.json в ссылку happ://routing/add/<base64>
и печатает готовый SQL для панели 3x-ui.

    python3 make-routing-link.py --repo antonsakss/onegate-geo

Опции:
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
ap.add_argument("--repo", required=True,
                help="GitHub-репозиторий в виде владелец/имя")
ap.add_argument("--profile", default="routing-profile.json")
ap.add_argument("--onadd", action="store_true")
args = ap.parse_args()

raw = open(args.profile, encoding="utf-8").read()
raw = raw.replace("__REPO__", args.repo).replace("__TS__", str(int(time.time())))
profile = json.loads(raw)  # заодно проверка, что JSON валиден

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
