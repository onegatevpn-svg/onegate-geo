#!/usr/bin/env python3
"""
Сборка geoip.dat для Xray/v2ray без Go и без MaxMind.

На вход — текстовые списки CIDR, на выход — бинарный geoip.dat в формате
GeoIPList (protobuf). Формат намеренно закодирован вручную: это три
простых сообщения, компилятор protobuf для них не нужен.

    message CIDR      { bytes ip = 1; uint32 prefix = 2; }
    message GeoIP     { string country_code = 1; repeated CIDR cidr = 2; }
    message GeoIPList { repeated GeoIP entry = 1; }

Использование:
    python3 build-geoip.py ru=ru.txt private=private.txt -o geoip.dat
"""
import argparse
import ipaddress
import sys


def varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def tag(field: int, wire: int) -> bytes:
    return varint((field << 3) | wire)


def bytes_field(field: int, value: bytes) -> bytes:
    return tag(field, 2) + varint(len(value)) + value


def varint_field(field: int, value: int) -> bytes:
    return tag(field, 0) + varint(value)


def encode_cidr(network) -> bytes:
    ip = network.network_address.packed
    return bytes_field(1, ip) + varint_field(2, network.prefixlen)


def encode_geoip(code: str, networks) -> bytes:
    body = bytes_field(1, code.upper().encode())
    body += b"".join(bytes_field(2, encode_cidr(n)) for n in networks)
    return body


def read_networks(path: str):
    """Читает CIDR по одному в строке. Пустые строки и # игнорируются.
    Голый адрес без маски трактуется как /32 (IPv4) или /128 (IPv6)."""
    v4, v6 = [], []
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.split("#")[0].strip()
            if not line:
                continue
            try:
                net = ipaddress.ip_network(line, strict=False)
            except ValueError as exc:
                print(f"{path}:{lineno}: пропущено — {exc}", file=sys.stderr)
                continue
            (v4 if net.version == 4 else v6).append(net)
    # схлопывать можно только внутри одной версии протокола
    return list(ipaddress.collapse_addresses(v4)) + list(ipaddress.collapse_addresses(v6))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("sources", nargs="+", metavar="КОД=ФАЙЛ",
                    help="например ru=ru.txt private=private.txt")
    ap.add_argument("-o", "--output", default="geoip.dat")
    args = ap.parse_args()

    blob = b""
    for src in args.sources:
        if "=" not in src:
            print(f"неверный аргумент: {src}", file=sys.stderr)
            return 2
        code, path = src.split("=", 1)
        nets = sorted(read_networks(path), key=lambda n: (n.version, n.network_address))
        blob += bytes_field(1, encode_geoip(code, nets))
        print(f"{code:<10} {len(nets):>7} диапазонов  ← {path}")

    with open(args.output, "wb") as fh:
        fh.write(blob)
    print(f"\n{args.output}: {len(blob)} байт ({len(blob)/1024:.1f} КБ)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
