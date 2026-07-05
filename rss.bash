#!/usr/bin/env bash
set -euo pipefail
set -x

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <baseline-command> <optimized-command> [runs]"
    echo "Example:"
    echo "  $0 './prog_baseline input.dat' './prog_opt input.dat' 20"
    exit 1
fi

BASE_CMD="$1"
OPT_CMD="$2"
RUNS="${3:-20}"

measure_rss() {
    local cmd="$1"

    for ((i=1; i<=RUNS; i++)); do
        ~/.nix-profile/bin/time -v bash -c "$cmd" \
            >/dev/null \
            2>time.out

        awk -F': *' \
            '/Maximum resident set size/ {print $2}' \
            time.out
    done

    rm -f time.out
}

echo "Collecting baseline measurements..."
baseline=$(measure_rss "$BASE_CMD")

echo "Collecting optimized measurements..."
optimized=$(measure_rss "$OPT_CMD")

paste \
    <(echo "$baseline") \
    <(echo "$optimized") |
awk '
{
    b[NR]=$1
    o[NR]=$2

    sb+=$1
    so+=$2
}
END{
    nb=NR

    mb=sb/nb
    mo=so/nb

    for(i=1;i<=nb;i++){
        vb+=(b[i]-mb)^2
        vo+=(o[i]-mo)^2
    }

    sdb=sqrt(vb/nb)
    sdo=sqrt(vo/nb)

    diff=((mo-mb)/mb)*100

    printf("\nResults (%d runs)\n", nb)
    printf("-----------------------------------------\n")
    printf("Baseline : %.1f ± %.1f kB\n", mb, sdb)
    printf("Optimized: %.1f ± %.1f kB\n", mo, sdo)
    printf("Change   : %+0.2f %%\n", diff)
}'
