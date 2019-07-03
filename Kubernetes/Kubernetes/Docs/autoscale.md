kubectl set resources deployment/xxxx --limit=cpu=200m
kubectl autoscale deployment xxxx --min=2 --max=5 --cpu-percent=10  #10%