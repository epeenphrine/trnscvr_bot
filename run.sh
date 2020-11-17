#/bin/sh
cd /mnt/raid-0/docker/python/trnscvr_bot/ &&
pipenv run python /mnt/raid-0/docker/python/trnscvr_bot/options_chains_req.py  &&
pipenv run python /mtn/raid-0/docker/python/trnscvr_bot/scan_dev.py
