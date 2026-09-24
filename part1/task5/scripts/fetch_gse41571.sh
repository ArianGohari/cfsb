#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
data_dir="$script_dir/../data/GSE41571"
mkdir -p "$data_dir"

fetch() {
  expected=$1
  url=$2
  target=$3
  temporary="$target.tmp"
  rm -f "$temporary"
  curl -fL --retry 3 -o "$temporary" "$url"
  actual=$(shasum -a 256 "$temporary" | awk '{print $1}')
  if [ "$actual" != "$expected" ]; then
    rm -f "$temporary"
    echo "SHA-256 mismatch for $target" >&2
    exit 1
  fi
  mv "$temporary" "$target"
}

fetch 1b48aaafaa16188eed06603fc3fc6267075ff9d1dec5889cf81bcb0e2aabca13 \
  https://ftp.ncbi.nlm.nih.gov/geo/series/GSE41nnn/GSE41571/matrix/GSE41571_series_matrix.txt.gz \
  "$data_dir/GSE41571_series_matrix.txt.gz"
fetch 2c1316cceaa641020e252eaba005ca3b1c88a85fab01c86fc3bb20e0b1cbf746 \
  https://ftp.ncbi.nlm.nih.gov/geo/series/GSE41nnn/GSE41571/soft/GSE41571_family.soft.gz \
  "$data_dir/GSE41571_family.soft.gz"
fetch c4491a4ffe99ff5c4464a59aef4ba2b62e959cb4272fec56eb93c591ae55a561 \
  https://ftp.ncbi.nlm.nih.gov/geo/series/GSE41nnn/GSE41571/suppl/GSE41571_matrix_NORMALIZED_RAW_ABSCALL.txt.gz \
  "$data_dir/GSE41571_matrix_NORMALIZED_RAW_ABSCALL.txt.gz"
fetch d7cd44352127b1e34f3a720ebea86093ef255a38f1612a85a2962b71bde8f394 \
  https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPLnnn/GPL570/annot/GPL570.annot.gz \
  "$data_dir/GPL570.annot.gz"

echo "GSE41571 inputs verified"
