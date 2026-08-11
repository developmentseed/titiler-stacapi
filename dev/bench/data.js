window.BENCHMARK_DATA = {
  "lastUpdate": 1786459782003,
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
            "name": "Mosaic-Z0",
            "value": 4.907532927104517,
            "unit": "iter/sec",
            "range": "stddev: 0.02010424691861108",
            "extra": "mean: 203.76837299999693 msec\nrounds: 5"
          },
          {
            "name": "Mosaic-Z1",
            "value": 11.032621040595368,
            "unit": "iter/sec",
            "range": "stddev: 0.011764435722685472",
            "extra": "mean: 90.64029266666769 msec\nrounds: 12"
          },
          {
            "name": "Mosaic-Z2",
            "value": 14.777808473132621,
            "unit": "iter/sec",
            "range": "stddev: 0.009986359866765037",
            "extra": "mean: 67.66903237500266 msec\nrounds: 16"
          },
          {
            "name": "Mosaic-Z3",
            "value": 24.607092958864765,
            "unit": "iter/sec",
            "range": "stddev: 0.0015195949191137822",
            "extra": "mean: 40.6386890833339 msec\nrounds: 24"
          },
          {
            "name": "Mosaic-Z4",
            "value": 33.80801282502966,
            "unit": "iter/sec",
            "range": "stddev: 0.0011132681289426226",
            "extra": "mean: 29.57878669697064 msec\nrounds: 33"
          },
          {
            "name": "Mosaic-Z5",
            "value": 32.37167720502467,
            "unit": "iter/sec",
            "range": "stddev: 0.0008222612369382531",
            "extra": "mean: 30.891201393938953 msec\nrounds: 33"
          },
          {
            "name": "Mosaic-Z6",
            "value": 32.60299854110482,
            "unit": "iter/sec",
            "range": "stddev: 0.0009053620212722445",
            "extra": "mean: 30.672025419356203 msec\nrounds: 31"
          },
          {
            "name": "Search-Z0",
            "value": 38.3155568272913,
            "unit": "iter/sec",
            "range": "stddev: 0.0010192078515418323",
            "extra": "mean: 26.099059567567675 msec\nrounds: 37"
          },
          {
            "name": "Search-Z1",
            "value": 66.19618025753955,
            "unit": "iter/sec",
            "range": "stddev: 0.00124003803932768",
            "extra": "mean: 15.106611833333133 msec\nrounds: 66"
          },
          {
            "name": "Search-Z2",
            "value": 69.01887690643296,
            "unit": "iter/sec",
            "range": "stddev: 0.0011070090182370752",
            "extra": "mean: 14.488789803920936 msec\nrounds: 51"
          },
          {
            "name": "Search-Z3",
            "value": 81.81017072128353,
            "unit": "iter/sec",
            "range": "stddev: 0.004640902446768674",
            "extra": "mean: 12.223419058821774 msec\nrounds: 85"
          },
          {
            "name": "Search-Z4",
            "value": 92.47008010104398,
            "unit": "iter/sec",
            "range": "stddev: 0.0007248390731696918",
            "extra": "mean: 10.814308789473085 msec\nrounds: 95"
          },
          {
            "name": "Search-Z5",
            "value": 95.26681462513402,
            "unit": "iter/sec",
            "range": "stddev: 0.0005415255684209729",
            "extra": "mean: 10.496834642103929 msec\nrounds: 95"
          },
          {
            "name": "Search-Z6",
            "value": 89.61106854010737,
            "unit": "iter/sec",
            "range": "stddev: 0.0015915445440008536",
            "extra": "mean: 11.159335741571125 msec\nrounds: 89"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "name": "vincentsarago",
            "username": "vincentsarago",
            "email": "vincent.sarago@gmail.com"
          },
          "committer": {
            "name": "vincentsarago",
            "username": "vincentsarago",
            "email": "vincent.sarago@gmail.com"
          },
          "id": "2a517015a965755b22aef0f2ea4b79042a9a2626",
          "message": "fix: bench names",
          "timestamp": "2026-08-06T15:18:35Z",
          "url": "https://github.com/developmentseed/titiler-stacapi/commit/2a517015a965755b22aef0f2ea4b79042a9a2626"
        },
        "date": 1786029890818,
        "tool": "pytest",
        "benches": [
          {
            "name": "Mosaic-Z0",
            "value": 4.7578507603981315,
            "unit": "iter/sec",
            "range": "stddev: 0.015203863177760719",
            "extra": "mean: 210.17893380000032 msec\nrounds: 5"
          },
          {
            "name": "Mosaic-Z1",
            "value": 10.937981120202805,
            "unit": "iter/sec",
            "range": "stddev: 0.0015522738112141784",
            "extra": "mean: 91.42454983332964 msec\nrounds: 12"
          },
          {
            "name": "Mosaic-Z2",
            "value": 14.09800133639426,
            "unit": "iter/sec",
            "range": "stddev: 0.01263345685860644",
            "extra": "mean: 70.93204037500556 msec\nrounds: 16"
          },
          {
            "name": "Mosaic-Z3",
            "value": 22.946718410169545,
            "unit": "iter/sec",
            "range": "stddev: 0.008193278795016292",
            "extra": "mean: 43.57921608332541 msec\nrounds: 24"
          },
          {
            "name": "Mosaic-Z4",
            "value": 32.311935319962835,
            "unit": "iter/sec",
            "range": "stddev: 0.0005237212749770901",
            "extra": "mean: 30.948316468750292 msec\nrounds: 32"
          },
          {
            "name": "Mosaic-Z5",
            "value": 29.028925018317892,
            "unit": "iter/sec",
            "range": "stddev: 0.007211985375418638",
            "extra": "mean: 34.448399290327764 msec\nrounds: 31"
          },
          {
            "name": "Mosaic-Z6",
            "value": 27.59527755944746,
            "unit": "iter/sec",
            "range": "stddev: 0.010556806926992558",
            "extra": "mean: 36.238084499992354 msec\nrounds: 30"
          },
          {
            "name": "Search-Z0",
            "value": 34.237438821117465,
            "unit": "iter/sec",
            "range": "stddev: 0.0010176100474286194",
            "extra": "mean: 29.20779224242689 msec\nrounds: 33"
          },
          {
            "name": "Search-Z1",
            "value": 59.8279886060441,
            "unit": "iter/sec",
            "range": "stddev: 0.0010696706891976597",
            "extra": "mean: 16.714584984375946 msec\nrounds: 64"
          },
          {
            "name": "Search-Z2",
            "value": 75.50199993528533,
            "unit": "iter/sec",
            "range": "stddev: 0.0009474037052908359",
            "extra": "mean: 13.244682271424933 msec\nrounds: 70"
          },
          {
            "name": "Search-Z3",
            "value": 87.77338349797941,
            "unit": "iter/sec",
            "range": "stddev: 0.004364867783815168",
            "extra": "mean: 11.392975411766148 msec\nrounds: 85"
          },
          {
            "name": "Search-Z4",
            "value": 89.75909634668926,
            "unit": "iter/sec",
            "range": "stddev: 0.0006933734205887431",
            "extra": "mean: 11.140932125002223 msec\nrounds: 96"
          },
          {
            "name": "Search-Z5",
            "value": 85.82431222594008,
            "unit": "iter/sec",
            "range": "stddev: 0.0012464192281575904",
            "extra": "mean: 11.65171003488396 msec\nrounds: 86"
          },
          {
            "name": "Search-Z6",
            "value": 90.82360281764575,
            "unit": "iter/sec",
            "range": "stddev: 0.0006077620040250392",
            "extra": "mean: 11.010353795453202 msec\nrounds: 88"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "vincent.sarago@gmail.com",
            "name": "vincentsarago",
            "username": "vincentsarago"
          },
          "committer": {
            "email": "vincent.sarago@gmail.com",
            "name": "vincentsarago",
            "username": "vincentsarago"
          },
          "distinct": true,
          "id": "a4951aa1d9a055f2e8b886958288354d46ee92d1",
          "message": "fix: cache",
          "timestamp": "2026-08-11T16:47:39+02:00",
          "tree_id": "1b10609587f835372c195e90419cce632396f223",
          "url": "https://github.com/developmentseed/titiler-stacapi/commit/a4951aa1d9a055f2e8b886958288354d46ee92d1"
        },
        "date": 1786459780956,
        "tool": "pytest",
        "benches": [
          {
            "name": "Mosaic-Z0",
            "value": 4.33238952689606,
            "unit": "iter/sec",
            "range": "stddev: 0.02034003998402436",
            "extra": "mean: 230.81950360000292 msec\nrounds: 5"
          },
          {
            "name": "Mosaic-Z1",
            "value": 10.650657800202373,
            "unit": "iter/sec",
            "range": "stddev: 0.012215727948257012",
            "extra": "mean: 93.89091441666626 msec\nrounds: 12"
          },
          {
            "name": "Mosaic-Z2",
            "value": 15.721561770985469,
            "unit": "iter/sec",
            "range": "stddev: 0.0013444105801169882",
            "extra": "mean: 63.60691224999826 msec\nrounds: 16"
          },
          {
            "name": "Mosaic-Z3",
            "value": 24.474286213560404,
            "unit": "iter/sec",
            "range": "stddev: 0.0012480135849065215",
            "extra": "mean: 40.85921000000125 msec\nrounds: 13"
          },
          {
            "name": "Mosaic-Z4",
            "value": 33.39679703754657,
            "unit": "iter/sec",
            "range": "stddev: 0.0008984321467312141",
            "extra": "mean: 29.942991205885505 msec\nrounds: 34"
          },
          {
            "name": "Mosaic-Z5",
            "value": 31.667325692502494,
            "unit": "iter/sec",
            "range": "stddev: 0.0006273999648759781",
            "extra": "mean: 31.578290181818492 msec\nrounds: 33"
          },
          {
            "name": "Mosaic-Z6",
            "value": 30.588464210536323,
            "unit": "iter/sec",
            "range": "stddev: 0.006819569246629647",
            "extra": "mean: 32.692063031250385 msec\nrounds: 32"
          },
          {
            "name": "Search-Z0",
            "value": 38.7433876243369,
            "unit": "iter/sec",
            "range": "stddev: 0.0009292764709884658",
            "extra": "mean: 25.810856027773983 msec\nrounds: 36"
          },
          {
            "name": "Search-Z1",
            "value": 70.66091385417174,
            "unit": "iter/sec",
            "range": "stddev: 0.0007880565033883692",
            "extra": "mean: 14.152095486109554 msec\nrounds: 72"
          },
          {
            "name": "Search-Z2",
            "value": 72.0021271753322,
            "unit": "iter/sec",
            "range": "stddev: 0.004441176414118388",
            "extra": "mean: 13.888478566263778 msec\nrounds: 83"
          },
          {
            "name": "Search-Z3",
            "value": 79.5989566421643,
            "unit": "iter/sec",
            "range": "stddev: 0.0009966181608178817",
            "extra": "mean: 12.562978739727486 msec\nrounds: 73"
          },
          {
            "name": "Search-Z4",
            "value": 91.16370589082251,
            "unit": "iter/sec",
            "range": "stddev: 0.000683968145516374",
            "extra": "mean: 10.96927763333358 msec\nrounds: 90"
          },
          {
            "name": "Search-Z5",
            "value": 87.87853747021812,
            "unit": "iter/sec",
            "range": "stddev: 0.004025487992413639",
            "extra": "mean: 11.37934277000113 msec\nrounds: 100"
          },
          {
            "name": "Search-Z6",
            "value": 88.08155892217103,
            "unit": "iter/sec",
            "range": "stddev: 0.004110665922564828",
            "extra": "mean: 11.353114230001324 msec\nrounds: 100"
          }
        ]
      }
    ]
  }
}