#!/usr/bin/env bash
count=0
while :
do
	output=$(python test_client.py TestSenecaClient.test_update_master_db_with_incomplete_sb 2>&1 >/dev/null)
	if [[ $output == *"FAIL:"* ]]; then
		echo "FAILURE!!"
		echo "$output"
		break
	else
		count=$((count+1))
		echo "Test passed (succ #$count)"
	fi
done

