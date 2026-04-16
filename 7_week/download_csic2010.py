"""
CSIC 2010 HTTP 데이터셋 준비
=============================
CSIC 2010 Web Application Attacks 데이터셋을 파싱하여
실습용 CSV 파일(csic2010_requests.csv)을 생성합니다.

============================================================
  사용 방법
============================================================

  [방법 1] 데이터 파일이 이미 있는 경우 (권장):
    1. 아래 3개 파일을 이 스크립트와 같은 폴더(또는 data/ 폴더)에 배치:
       - normalTrafficTraining.txt
       - normalTrafficTest.txt
       - anomalousTrafficTest.txt
    2. python download_csic2010.py

  [방법 2] 특정 폴더에 파일이 있는 경우:
    python download_csic2010.py --path "데이터_폴더_경로"

실행 결과: csic2010_requests.csv 파일이 생성됩니다.
"""

import os
import sys
import argparse
import re
import pandas as pd


# ============================================================
# HTTP 요청 파싱
# ============================================================
def parse_http_requests(file_path, label):
    """
    원시 HTTP 텍스트 파일을 파싱하여 요청 목록을 반환합니다.

    Parameters:
        file_path: HTTP 요청 텍스트 파일 경로
        label: 'Normal' 또는 'Anomalous'

    Returns:
        list of dict — 각 HTTP 요청의 파싱 결과
    """
    with open(file_path, "r", encoding="latin-1") as f:
        content = f.read()

    # 요청 구분: 빈 줄 2개(\n\n)로 분리
    # 일부 파일은 \r\n 사용 가능
    content = content.replace("\r\n", "\n")
    raw_requests = re.split(r"\n\n+", content.strip())

    requests = []
    for raw in raw_requests:
        raw = raw.strip()
        if not raw:
            continue

        lines = raw.split("\n")
        if len(lines) < 2:
            continue

        # 첫 줄 파싱: METHOD URL HTTP/VERSION
        first_line = lines[0].strip()
        parts = first_line.split(" ", 2)
        if len(parts) < 3:
            continue

        method = parts[0]
        url = parts[1]
        http_version = parts[2]

        # 헤더 파싱
        headers = {}
        body = ""
        body_started = False

        for line in lines[1:]:
            if body_started:
                body += line
            elif line.strip() == "":
                # 빈 줄 이후는 body (POST 요청의 경우)
                body_started = True
            elif ": " in line:
                key, value = line.split(": ", 1)
                headers[key.strip()] = value.strip()
            else:
                # 헤더도 아니고 빈 줄도 아닌 경우 → body로 처리
                body = line.strip()

        request = {
            "method": method,
            "url": url,
            "http_version": http_version,
            "host": headers.get("Host", ""),
            "user_agent": headers.get("User-Agent", ""),
            "cookie": headers.get("Cookie", ""),
            "content_type": headers.get("Content-Type", ""),
            "content_length": headers.get("Content-Length", ""),
            "pragma": headers.get("Pragma", ""),
            "accept": headers.get("Accept", ""),
            "body": body,
            "label": label,
            "raw_request": raw,
        }
        requests.append(request)

    return requests


def find_data_files(search_path):
    """데이터 파일 3개를 찾아서 경로를 반환"""
    required_files = {
        "normalTrafficTraining.txt": None,
        "normalTrafficTest.txt": None,
        "anomalousTrafficTest.txt": None,
    }

    # 지정된 경로에서 검색
    for fname in required_files:
        # 직접 경로
        direct = os.path.join(search_path, fname)
        if os.path.exists(direct):
            required_files[fname] = direct
            continue

        # data/ 하위 폴더
        data_path = os.path.join(search_path, "data", fname)
        if os.path.exists(data_path):
            required_files[fname] = data_path
            continue

    return required_files


def main():
    parser = argparse.ArgumentParser(
        description="CSIC 2010 HTTP 데이터셋 파싱 및 CSV 변환"
    )
    parser.add_argument(
        "--path", type=str, default=None,
        help="데이터 파일이 있는 폴더 경로"
    )
    args = parser.parse_args()

    print("=" * 65)
    print("  CSIC 2010 HTTP 데이터셋 → CSV 변환")
    print("=" * 65)

    # 데이터 파일 검색
    script_dir = os.path.dirname(os.path.abspath(__file__))
    search_path = args.path if args.path else script_dir

    files = find_data_files(search_path)
    missing = [f for f, p in files.items() if p is None]

    if missing:
        print(f"\n  !! 다음 파일을 찾을 수 없습니다:")
        for f in missing:
            print(f"     - {f}")
        print(f"\n  검색 경로: {search_path}")
        print(f"\n  해결 방법:")
        print(f"    1. 위 3개 파일을 이 폴더에 복사하세요")
        print(f"    2. 또는: python download_csic2010.py --path \"파일이_있는_폴더\"")
        sys.exit(1)

    # 파일 파싱
    all_requests = []

    file_configs = [
        ("normalTrafficTraining.txt", "Normal"),
        ("normalTrafficTest.txt", "Normal"),
        ("anomalousTrafficTest.txt", "Anomalous"),
    ]

    for fname, label in file_configs:
        fpath = files[fname]
        print(f"\n  파싱 중: {fname} ({label})")
        requests = parse_http_requests(fpath, label)
        print(f"    → {len(requests):,}건 파싱 완료")
        all_requests.extend(requests)

    # DataFrame 생성
    df = pd.DataFrame(all_requests)
    print(f"\n  전체 데이터: {len(df):,}건")

    # 라벨 분포 확인
    print(f"\n  라벨 분포:")
    for label, count in df["label"].value_counts().items():
        pct = count / len(df) * 100
        bar = "█" * int(pct / 2)
        print(f"    {label:12s}: {count:>8,}건 ({pct:5.1f}%) {bar}")

    # 메서드 분포
    print(f"\n  HTTP 메서드 분포:")
    for method, count in df["method"].value_counts().items():
        print(f"    {method:6s}: {count:>8,}건")

    # CSV 저장
    output_path = os.path.join(script_dir, "csic2010_requests.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    file_size = os.path.getsize(output_path) / 1024 / 1024
    print(f"\n{'=' * 65}")
    print(f"  저장 완료: csic2010_requests.csv")
    print(f"  크기: {len(df):,}건 x {df.shape[1]}열")
    print(f"  파일 크기: {file_size:.1f} MB")
    print(f"{'=' * 65}")
    print(f"\n  >> 다음 단계: python data_load_explore.py")


if __name__ == "__main__":
    main()
