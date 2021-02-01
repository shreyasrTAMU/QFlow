tc qdisc replace dev wlan0 root pfifo
tc qdisc replace dev wlan0 root handle 1: htb default 30
tc class add dev wlan0 parent 1: classid 1:1 htb rate 11mbit ceil 11mbit
tc class add dev wlan0 parent 1:1 classid 1:10 htb rate 11mbit ceil 11mbit
tc class add dev wlan0 parent 1: classid 1:30 htb rate 4.3mbit ceil 4.3mbit

tc qdisc add dev wlan0 parent 1:10 handle 10: netem loss 0% delay 0ms
tc qdisc add dev wlan0 parent 1:30 handle 30: sfq perturb 10

