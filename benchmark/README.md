
### Start DB
```bash
$ docker compose up api
```

### Add items/collections to the db

```bash
uv pip install pypgstac==0.9.11 "psycopg[pool]"
uv run pypgstac load collections stac/collection.json --dsn postgresql://username:password@127.0.0.1:5439/postgis --method upsert
uv run pypgstac load items stac/items.json --dsn postgresql://username:password@127.0.0.1:5439/postgis --method upsert

# Create Collection Search in cache
curl http://127.0.0.1:8081/collections/world/info | jq
```


### Benchmark 

```bash
uv run pytest benchmarks.py --benchmark-only --benchmark-columns 'min, max, mean, median'

-------------------------------------------- benchmark: 7 tests -------------------------------------------
Name (time in ms)                    Min                Max               Mean             Median          
-----------------------------------------------------------------------------------------------------------
test_benchmark_tile[4/5/9]       14.1862 (1.0)      37.1480 (1.0)      16.0601 (1.0)      15.8112 (1.0)    
test_benchmark_tile[6/43/31]     15.1011 (1.06)     38.5358 (1.04)     19.1328 (1.19)     16.9307 (1.07)   
test_benchmark_tile[5/16/5]      15.1612 (1.07)     41.2818 (1.11)     17.8598 (1.11)     16.2121 (1.03)   
test_benchmark_tile[3/5/0]       18.4070 (1.30)     75.9044 (2.04)     22.8204 (1.42)     20.0948 (1.27)   
test_benchmark_tile[2/2/1]       26.2479 (1.85)     53.0078 (1.43)     30.8800 (1.92)     29.3396 (1.86)   
test_benchmark_tile[1/1/1]       34.5101 (2.43)     39.5436 (1.06)     37.9058 (2.36)     38.3615 (2.43)   
test_benchmark_tile[0/0/0]       78.7385 (5.55)     98.5915 (2.65)     87.7893 (5.47)     87.3070 (5.52)   
-----------------------------------------------------------------------------------------------------------
```

### Siege
```
# 50 concurrents / repeat 10 times (500 tiles)
$ siege --file urls.txt -b -c 50 -r 10

Transactions:                 500    hits
Availability:                 100.00 %
Elapsed time:                   7.58 secs
Data transferred:               5.40 MB
Response time:                643.34 ms
Transaction rate:              65.96 trans/sec
Throughput:                     0.71 MB/sec
Concurrency:                   42.44
Successful transactions:      500
Failed transactions:            0
Longest transaction:         3300.00 ms
Shortest transaction:          60.00 ms


# 10 concurrents / repeat 100 times (1000 tiles)
$ siege --file urls.txt -b -c 10 -r 100

Transactions:                1000    hits
Availability:                 100.00 %
Elapsed time:                  16.37 secs
Data transferred:              11.45 MB
Response time:                119.98 ms
Transaction rate:              61.09 trans/sec
Throughput:                     0.70 MB/sec
Concurrency:                    7.33
Successful transactions:     1000
Failed transactions:            0
Longest transaction:          610.00 ms
Shortest transaction:          20.00 ms

# 200 concurrents / repeat 1 time (200 tiles)
$ siege --file urls.txt -b -c 200 -r 1

Transactions:                 200    hits
Availability:                 100.00 %
Elapsed time:                   2.71 secs
Data transferred:               2.08 MB
Response time:               1482.95 ms
Transaction rate:              73.80 trans/sec
Throughput:                     0.77 MB/sec
Concurrency:                  109.44
Successful transactions:      200
Failed transactions:            0
Longest transaction:         2710.00 ms
Shortest transaction:         330.00 ms
```