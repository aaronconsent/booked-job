#!/bin/zsh
cd /Users/aaronphillips/GIT/booked-job
# 1) wait for the lesson re-render (4-10) to finish
while ! grep -q "RE-RENDER 4-10 DONE" /tmp/rerender_rest_main.log 2>/dev/null; do sleep 20; done
echo "LESSONS 4-10 DONE — starting shorts"
# 2) batch-render the 10 vertical shorts (3 at a time)
for batch in "1 2 3" "4 5 6" "7 8 9" "10"; do
  for n in ${(z)batch}; do
    DOODLE_W=1080 DOODLE_H=1920 python3 -u scripts/doodle_engine.py content/course/shorts/L${n}.json content/course/shorts/L${n}.mp4 > /tmp/short_L${n}.log 2>&1 &
  done
  wait
done
echo "ALL SHORTS DONE"
