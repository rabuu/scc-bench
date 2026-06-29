#!/bin/bash

set -e

echo "benchmark,main,lin" > file_sizes.csv

dir="$1"

for f in "$dir"/*_main; do
	base=${f%_main}
	benchmark=$(basename "$base")
	if [[ -f "${base}_lin" ]]; then
		# s1=$(stat -c%s "$f")
		# s2=$(stat -c%s "${base}_lin")
		s1=$(wc -l < "$f")
		s2=$(wc -l < "${base}_lin")
		echo "$benchmark,$s1,$s2" >> file_sizes.csv
	fi
done
