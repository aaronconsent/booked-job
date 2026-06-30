#!/bin/zsh
cd /Users/aaronphillips/GIT/booked-job
for batch in "4 5 6" "7 8 9" "10"; do
  for n in ${(z)batch}; do
    python3 -u scripts/doodle_engine.py content/course/course${n}_intro.json content/course/course${n}-intro.mp4 > /tmp/rerender_c${n}.log 2>&1 &
  done
  wait
  echo "batch [$batch] done"
done
echo "RE-RENDER 4-10 DONE"
