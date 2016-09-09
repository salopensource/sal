#!/bin/bash
# Wait for all monit services to be stop before release

total_services=$(monit summary | grep -c "^Process")

command_return=1
while [ $command_return != 0 ] ; do
   sleep 1
   command_return=$(/usr/bin/monit stop all 2>&1 | grep -c "Action failed")
done

while [ $total_services != $(monit summary | grep "^Process" | grep -c "Not monitored") ] ; do
   sleep 1
done
