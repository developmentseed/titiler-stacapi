window.BENCHMARK_DATA = {
  "lastUpdate": 1786026721734,
  "repoUrl": "https://github.com/developmentseed/titiler-stacapi",
  "entries": {
    "TiTiler-STACapi Benchmarks": [
      {
        "commit": {
          "author": {
            "email": "vincent.sarago@gmail.com",
            "name": "Vincent Sarago",
            "username": "vincentsarago"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "d3c4140b5f71c2abcacda9acdd686103c8ae90f4",
          "message": "Merge pull request #91 from developmentseed/ci/add-benchmark\n\nci: add benchmark",
          "timestamp": "2026-08-06T16:30:09+02:00",
          "tree_id": "79d79fd45b28c784d055115500185ddb0d1b24bb",
          "url": "https://github.com/developmentseed/titiler-stacapi/commit/d3c4140b5f71c2abcacda9acdd686103c8ae90f4"
        },
        "date": 1786026721399,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark/benchmarks.py::test_benchmark_tile[tile0]",
            "value": 4.907532927104517,
            "unit": "iter/sec",
            "range": "stddev: 0.02010424691861108",
            "extra": "mean: 203.76837299999693 msec\nrounds: 5"
          },
          {
            "name": "benchmark/benchmarks.py::test_benchmark_tile[tile1]",
            "value": 11.032621040595368,
            "unit": "iter/sec",
            "range": "stddev: 0.011764435722685472",
            "extra": "mean: 90.64029266666769 msec\nrounds: 12"
          },
          {
            "name": "benchmark/benchmarks.py::test_benchmark_tile[tile2]",
            "value": 14.777808473132621,
            "unit": "iter/sec",
            "range": "stddev: 0.009986359866765037",
            "extra": "mean: 67.66903237500266 msec\nrounds: 16"
          },
          {
            "name": "benchmark/benchmarks.py::test_benchmark_tile[tile3]",
            "value": 24.607092958864765,
            "unit": "iter/sec",
            "range": "stddev: 0.0015195949191137822",
            "extra": "mean: 40.6386890833339 msec\nrounds: 24"
          },
          {
            "name": "benchmark/benchmarks.py::test_benchmark_tile[tile4]",
            "value": 33.80801282502966,
            "unit": "iter/sec",
            "range": "stddev: 0.0011132681289426226",
            "extra": "mean: 29.57878669697064 msec\nrounds: 33"
          },
          {
            "name": "benchmark/benchmarks.py::test_benchmark_tile[tile5]",
            "value": 32.37167720502467,
            "unit": "iter/sec",
            "range": "stddev: 0.0008222612369382531",
            "extra": "mean: 30.891201393938953 msec\nrounds: 33"
          },
          {
            "name": "benchmark/benchmarks.py::test_benchmark_tile[tile6]",
            "value": 32.60299854110482,
            "unit": "iter/sec",
            "range": "stddev: 0.0009053620212722445",
            "extra": "mean: 30.672025419356203 msec\nrounds: 31"
          },
          {
            "name": "benchmark/benchmarks.py::test_benchmark_search[tile0]",
            "value": 38.3155568272913,
            "unit": "iter/sec",
            "range": "stddev: 0.0010192078515418323",
            "extra": "mean: 26.099059567567675 msec\nrounds: 37"
          },
          {
            "name": "benchmark/benchmarks.py::test_benchmark_search[tile1]",
            "value": 66.19618025753955,
            "unit": "iter/sec",
            "range": "stddev: 0.00124003803932768",
            "extra": "mean: 15.106611833333133 msec\nrounds: 66"
          },
          {
            "name": "benchmark/benchmarks.py::test_benchmark_search[tile2]",
            "value": 69.01887690643296,
            "unit": "iter/sec",
            "range": "stddev: 0.0011070090182370752",
            "extra": "mean: 14.488789803920936 msec\nrounds: 51"
          },
          {
            "name": "benchmark/benchmarks.py::test_benchmark_search[tile3]",
            "value": 81.81017072128353,
            "unit": "iter/sec",
            "range": "stddev: 0.004640902446768674",
            "extra": "mean: 12.223419058821774 msec\nrounds: 85"
          },
          {
            "name": "benchmark/benchmarks.py::test_benchmark_search[tile4]",
            "value": 92.47008010104398,
            "unit": "iter/sec",
            "range": "stddev: 0.0007248390731696918",
            "extra": "mean: 10.814308789473085 msec\nrounds: 95"
          },
          {
            "name": "benchmark/benchmarks.py::test_benchmark_search[tile5]",
            "value": 95.26681462513402,
            "unit": "iter/sec",
            "range": "stddev: 0.0005415255684209729",
            "extra": "mean: 10.496834642103929 msec\nrounds: 95"
          },
          {
            "name": "benchmark/benchmarks.py::test_benchmark_search[tile6]",
            "value": 89.61106854010737,
            "unit": "iter/sec",
            "range": "stddev: 0.0015915445440008536",
            "extra": "mean: 11.159335741571125 msec\nrounds: 89"
          }
        ]
      }
    ]
  }
}