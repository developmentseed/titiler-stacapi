window.BENCHMARK_DATA = {
  "lastUpdate": 1787559126564,
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
      },
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
          "id": "ce77e39af67ba424e78aacabe8102a297c4e5dd9",
          "message": "Merge pull request #96 from developmentseed/dependabot/uv/all-ac73a126f9\n\nchore(deps): bump the all group with 4 updates",
          "timestamp": "2026-08-20T10:31:20+02:00",
          "tree_id": "5c63b8f17c72e7744449d957f6f4f09b81bf621b",
          "url": "https://github.com/developmentseed/titiler-stacapi/commit/ce77e39af67ba424e78aacabe8102a297c4e5dd9"
        },
        "date": 1787214789170,
        "tool": "pytest",
        "benches": [
          {
            "name": "Mosaic-Z0",
            "value": 4.858699287875337,
            "unit": "iter/sec",
            "range": "stddev: 0.019544397034015542",
            "extra": "mean: 205.81640079999488 msec\nrounds: 5"
          },
          {
            "name": "Mosaic-Z1",
            "value": 11.380150470701162,
            "unit": "iter/sec",
            "range": "stddev: 0.0013751506785972432",
            "extra": "mean: 87.87230033333533 msec\nrounds: 12"
          },
          {
            "name": "Mosaic-Z2",
            "value": 14.052821813383341,
            "unit": "iter/sec",
            "range": "stddev: 0.015306843776402982",
            "extra": "mean: 71.16008537499852 msec\nrounds: 16"
          },
          {
            "name": "Mosaic-Z3",
            "value": 23.191587709829307,
            "unit": "iter/sec",
            "range": "stddev: 0.007655148727769612",
            "extra": "mean: 43.1190831999902 msec\nrounds: 25"
          },
          {
            "name": "Mosaic-Z4",
            "value": 33.18974106994016,
            "unit": "iter/sec",
            "range": "stddev: 0.0006971847177030259",
            "extra": "mean: 30.129792151518068 msec\nrounds: 33"
          },
          {
            "name": "Mosaic-Z5",
            "value": 31.927949617407513,
            "unit": "iter/sec",
            "range": "stddev: 0.00043606482959516975",
            "extra": "mean: 31.320520483870588 msec\nrounds: 31"
          },
          {
            "name": "Mosaic-Z6",
            "value": 31.38646533873952,
            "unit": "iter/sec",
            "range": "stddev: 0.0007005365446119421",
            "extra": "mean: 31.860867071441945 msec\nrounds: 14"
          },
          {
            "name": "Search-Z0",
            "value": 37.506368514388775,
            "unit": "iter/sec",
            "range": "stddev: 0.001272711054448957",
            "extra": "mean: 26.662138714292333 msec\nrounds: 35"
          },
          {
            "name": "Search-Z1",
            "value": 61.847456616693684,
            "unit": "iter/sec",
            "range": "stddev: 0.005118386970654853",
            "extra": "mean: 16.168813637682927 msec\nrounds: 69"
          },
          {
            "name": "Search-Z2",
            "value": 72.4768595634615,
            "unit": "iter/sec",
            "range": "stddev: 0.0009782788372637377",
            "extra": "mean: 13.797507315067776 msec\nrounds: 73"
          },
          {
            "name": "Search-Z3",
            "value": 84.11812967777479,
            "unit": "iter/sec",
            "range": "stddev: 0.0007089493819449528",
            "extra": "mean: 11.888043681316114 msec\nrounds: 91"
          },
          {
            "name": "Search-Z4",
            "value": 91.92315122901968,
            "unit": "iter/sec",
            "range": "stddev: 0.0005022467881516503",
            "extra": "mean: 10.878652294116577 msec\nrounds: 85"
          },
          {
            "name": "Search-Z5",
            "value": 89.87203455629854,
            "unit": "iter/sec",
            "range": "stddev: 0.0009910454766084793",
            "extra": "mean: 11.126931808510133 msec\nrounds: 94"
          },
          {
            "name": "Search-Z6",
            "value": 89.33576624404067,
            "unit": "iter/sec",
            "range": "stddev: 0.0008911825411179905",
            "extra": "mean: 11.19372499999917 msec\nrounds: 63"
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
          "id": "11a4efd6c03928a957b501708777c1cf8469c5d9",
          "message": "ci: update lockfile",
          "timestamp": "2026-08-20T10:38:00+02:00",
          "tree_id": "08435ff2afaebf696eb9dd16f87070877f95d273",
          "url": "https://github.com/developmentseed/titiler-stacapi/commit/11a4efd6c03928a957b501708777c1cf8469c5d9"
        },
        "date": 1787215232104,
        "tool": "pytest",
        "benches": [
          {
            "name": "Mosaic-Z0",
            "value": 5.491690260963482,
            "unit": "iter/sec",
            "range": "stddev: 0.0452485422371208",
            "extra": "mean: 182.09329959999536 msec\nrounds: 5"
          },
          {
            "name": "Mosaic-Z1",
            "value": 14.604033593577121,
            "unit": "iter/sec",
            "range": "stddev: 0.006865821388783135",
            "extra": "mean: 68.47423306666465 msec\nrounds: 15"
          },
          {
            "name": "Mosaic-Z2",
            "value": 16.877043229786963,
            "unit": "iter/sec",
            "range": "stddev: 0.015034491707313",
            "extra": "mean: 59.25208499999931 msec\nrounds: 13"
          },
          {
            "name": "Mosaic-Z3",
            "value": 31.39243058454244,
            "unit": "iter/sec",
            "range": "stddev: 0.002569833035074417",
            "extra": "mean: 31.854812812500022 msec\nrounds: 32"
          },
          {
            "name": "Mosaic-Z4",
            "value": 34.979447572436335,
            "unit": "iter/sec",
            "range": "stddev: 0.017252491285075677",
            "extra": "mean: 28.588215921054054 msec\nrounds: 38"
          },
          {
            "name": "Mosaic-Z5",
            "value": 28.152153928557908,
            "unit": "iter/sec",
            "range": "stddev: 0.03150392920797831",
            "extra": "mean: 35.52126073684142 msec\nrounds: 38"
          },
          {
            "name": "Mosaic-Z6",
            "value": 20.86761553403673,
            "unit": "iter/sec",
            "range": "stddev: 0.05956301869745017",
            "extra": "mean: 47.9211435714311 msec\nrounds: 7"
          },
          {
            "name": "Search-Z0",
            "value": 37.69925881040771,
            "unit": "iter/sec",
            "range": "stddev: 0.015425835972673002",
            "extra": "mean: 26.525720439997826 msec\nrounds: 50"
          },
          {
            "name": "Search-Z1",
            "value": 59.44141582335149,
            "unit": "iter/sec",
            "range": "stddev: 0.020486056959726676",
            "extra": "mean: 16.823287032257248 msec\nrounds: 62"
          },
          {
            "name": "Search-Z2",
            "value": 69.33780273071785,
            "unit": "iter/sec",
            "range": "stddev: 0.019929918768538783",
            "extra": "mean: 14.422147235954776 msec\nrounds: 89"
          },
          {
            "name": "Search-Z3",
            "value": 57.070642276570744,
            "unit": "iter/sec",
            "range": "stddev: 0.022508870792946188",
            "extra": "mean: 17.52214378723631 msec\nrounds: 94"
          },
          {
            "name": "Search-Z4",
            "value": 62.37280654766605,
            "unit": "iter/sec",
            "range": "stddev: 0.019827888069174453",
            "extra": "mean: 16.032627924731717 msec\nrounds: 93"
          },
          {
            "name": "Search-Z5",
            "value": 70.31198509333723,
            "unit": "iter/sec",
            "range": "stddev: 0.014278407212318905",
            "extra": "mean: 14.22232637398201 msec\nrounds: 123"
          },
          {
            "name": "Search-Z6",
            "value": 69.28031893625224,
            "unit": "iter/sec",
            "range": "stddev: 0.014639399270158846",
            "extra": "mean: 14.434113689923143 msec\nrounds: 129"
          }
        ]
      },
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
          "id": "a6d0ac94205d104bcf34a5662558da7ce3cf855a",
          "message": "Merge pull request #97 from developmentseed/refactor/docker-image-with-wolfi\n\nrefactor: use wolfi docker image",
          "timestamp": "2026-08-21T09:12:43+02:00",
          "tree_id": "2e3c35f5d71812e466b6e5e31873afc83feeee98",
          "url": "https://github.com/developmentseed/titiler-stacapi/commit/a6d0ac94205d104bcf34a5662558da7ce3cf855a"
        },
        "date": 1787296450871,
        "tool": "pytest",
        "benches": [
          {
            "name": "Mosaic-Z0",
            "value": 4.597304893449029,
            "unit": "iter/sec",
            "range": "stddev: 0.017729690914231672",
            "extra": "mean: 217.51874699999973 msec\nrounds: 5"
          },
          {
            "name": "Mosaic-Z1",
            "value": 10.346753078032824,
            "unit": "iter/sec",
            "range": "stddev: 0.01254508529665259",
            "extra": "mean: 96.64867736363578 msec\nrounds: 11"
          },
          {
            "name": "Mosaic-Z2",
            "value": 14.17216032352715,
            "unit": "iter/sec",
            "range": "stddev: 0.010532646876816248",
            "extra": "mean: 70.56087266666775 msec\nrounds: 15"
          },
          {
            "name": "Mosaic-Z3",
            "value": 24.074281605155896,
            "unit": "iter/sec",
            "range": "stddev: 0.001087168770740529",
            "extra": "mean: 41.53810345833264 msec\nrounds: 24"
          },
          {
            "name": "Mosaic-Z4",
            "value": 33.690635096370556,
            "unit": "iter/sec",
            "range": "stddev: 0.0007143027929107689",
            "extra": "mean: 29.681838799997234 msec\nrounds: 15"
          },
          {
            "name": "Mosaic-Z5",
            "value": 31.262916560960086,
            "unit": "iter/sec",
            "range": "stddev: 0.000999816734484986",
            "extra": "mean: 31.9867789062509 msec\nrounds: 32"
          },
          {
            "name": "Mosaic-Z6",
            "value": 31.43729297196913,
            "unit": "iter/sec",
            "range": "stddev: 0.0007557085212113781",
            "extra": "mean: 31.809354606061152 msec\nrounds: 33"
          },
          {
            "name": "Search-Z0",
            "value": 38.48343697619611,
            "unit": "iter/sec",
            "range": "stddev: 0.0011075782897541145",
            "extra": "mean: 25.98520502777725 msec\nrounds: 36"
          },
          {
            "name": "Search-Z1",
            "value": 66.70381469777332,
            "unit": "iter/sec",
            "range": "stddev: 0.004793580967057416",
            "extra": "mean: 14.991646347826963 msec\nrounds: 69"
          },
          {
            "name": "Search-Z2",
            "value": 80.29981968553848,
            "unit": "iter/sec",
            "range": "stddev: 0.0006468406950351814",
            "extra": "mean: 12.453328088607078 msec\nrounds: 79"
          },
          {
            "name": "Search-Z3",
            "value": 88.4429609914159,
            "unit": "iter/sec",
            "range": "stddev: 0.0007813299030592954",
            "extra": "mean: 11.306722307692278 msec\nrounds: 78"
          },
          {
            "name": "Search-Z4",
            "value": 92.73318822598085,
            "unit": "iter/sec",
            "range": "stddev: 0.0041402534470526805",
            "extra": "mean: 10.78362578846213 msec\nrounds: 104"
          },
          {
            "name": "Search-Z5",
            "value": 89.08812200951328,
            "unit": "iter/sec",
            "range": "stddev: 0.0040344742982022785",
            "extra": "mean: 11.224840948978754 msec\nrounds: 98"
          },
          {
            "name": "Search-Z6",
            "value": 92.94586219543204,
            "unit": "iter/sec",
            "range": "stddev: 0.0009586408372062337",
            "extra": "mean: 10.758951247311646 msec\nrounds: 93"
          }
        ]
      },
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
          "id": "31e6b4e65c1e2dcd1694033fc236b33e8a805f06",
          "message": "Merge pull request #98 from developmentseed/feat/release-please\n\nci: setup release please",
          "timestamp": "2026-08-24T09:05:34+02:00",
          "tree_id": "ea6adae85e898726fbf86cd01e166212b24ed010",
          "url": "https://github.com/developmentseed/titiler-stacapi/commit/31e6b4e65c1e2dcd1694033fc236b33e8a805f06"
        },
        "date": 1787555233056,
        "tool": "pytest",
        "benches": [
          {
            "name": "Mosaic-Z0",
            "value": 4.594329042872586,
            "unit": "iter/sec",
            "range": "stddev: 0.020658041734541752",
            "extra": "mean: 217.65963880000072 msec\nrounds: 5"
          },
          {
            "name": "Mosaic-Z1",
            "value": 10.837917717209017,
            "unit": "iter/sec",
            "range": "stddev: 0.001823364393931655",
            "extra": "mean: 92.26864662500134 msec\nrounds: 8"
          },
          {
            "name": "Mosaic-Z2",
            "value": 14.123218824836213,
            "unit": "iter/sec",
            "range": "stddev: 0.010485047127047866",
            "extra": "mean: 70.80538879999949 msec\nrounds: 15"
          },
          {
            "name": "Mosaic-Z3",
            "value": 24.36718208812801,
            "unit": "iter/sec",
            "range": "stddev: 0.0013153957948487816",
            "extra": "mean: 41.038803599994935 msec\nrounds: 25"
          },
          {
            "name": "Mosaic-Z4",
            "value": 33.53427934890251,
            "unit": "iter/sec",
            "range": "stddev: 0.0028405195136314756",
            "extra": "mean: 29.820232294114515 msec\nrounds: 34"
          },
          {
            "name": "Mosaic-Z5",
            "value": 30.41635354910937,
            "unit": "iter/sec",
            "range": "stddev: 0.0071321540089745875",
            "extra": "mean: 32.87705077419714 msec\nrounds: 31"
          },
          {
            "name": "Mosaic-Z6",
            "value": 32.01088898404981,
            "unit": "iter/sec",
            "range": "stddev: 0.0005979413054392347",
            "extra": "mean: 31.23936984375142 msec\nrounds: 32"
          },
          {
            "name": "Search-Z0",
            "value": 38.677098839139894,
            "unit": "iter/sec",
            "range": "stddev: 0.0012545853294714435",
            "extra": "mean: 25.855093324322308 msec\nrounds: 37"
          },
          {
            "name": "Search-Z1",
            "value": 69.20990450463488,
            "unit": "iter/sec",
            "range": "stddev: 0.005004464513261314",
            "extra": "mean: 14.448799014497 msec\nrounds: 69"
          },
          {
            "name": "Search-Z2",
            "value": 79.84739067921187,
            "unit": "iter/sec",
            "range": "stddev: 0.0007021206710233706",
            "extra": "mean: 12.523890780821073 msec\nrounds: 73"
          },
          {
            "name": "Search-Z3",
            "value": 91.66480883519552,
            "unit": "iter/sec",
            "range": "stddev: 0.0005068806548823041",
            "extra": "mean: 10.909312010871082 msec\nrounds: 92"
          },
          {
            "name": "Search-Z4",
            "value": 93.60475137572412,
            "unit": "iter/sec",
            "range": "stddev: 0.003934866239104598",
            "extra": "mean: 10.683218376234526 msec\nrounds: 101"
          },
          {
            "name": "Search-Z5",
            "value": 93.72431489790578,
            "unit": "iter/sec",
            "range": "stddev: 0.004349056444084169",
            "extra": "mean: 10.669589861385527 msec\nrounds: 101"
          },
          {
            "name": "Search-Z6",
            "value": 98.35407085203634,
            "unit": "iter/sec",
            "range": "stddev: 0.0004403625931088497",
            "extra": "mean: 10.167347333334051 msec\nrounds: 105"
          }
        ]
      },
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
          "id": "0d3ac27fda802933d0370431241f3d4f6cfb340b",
          "message": "Merge pull request #100 from developmentseed/dependabot/github_actions/astral-sh/setup-uv-10.0.1\n\nchore(deps): bump astral-sh/setup-uv from 9.0.0 to 10.0.1",
          "timestamp": "2026-08-24T10:10:30+02:00",
          "tree_id": "ee7d8ec7bca5d8f2fe4494139c957adcc7ab9fe7",
          "url": "https://github.com/developmentseed/titiler-stacapi/commit/0d3ac27fda802933d0370431241f3d4f6cfb340b"
        },
        "date": 1787559125486,
        "tool": "pytest",
        "benches": [
          {
            "name": "Mosaic-Z0",
            "value": 4.632745292394769,
            "unit": "iter/sec",
            "range": "stddev: 0.01789513503641835",
            "extra": "mean: 215.85473340000476 msec\nrounds: 5"
          },
          {
            "name": "Mosaic-Z1",
            "value": 11.029743711331507,
            "unit": "iter/sec",
            "range": "stddev: 0.0013423881656542832",
            "extra": "mean: 90.66393799999548 msec\nrounds: 11"
          },
          {
            "name": "Mosaic-Z2",
            "value": 14.25556779212326,
            "unit": "iter/sec",
            "range": "stddev: 0.01009516657314718",
            "extra": "mean: 70.14803019999931 msec\nrounds: 15"
          },
          {
            "name": "Mosaic-Z3",
            "value": 22.356140431694524,
            "unit": "iter/sec",
            "range": "stddev: 0.01145154748843439",
            "extra": "mean: 44.73044008000102 msec\nrounds: 25"
          },
          {
            "name": "Mosaic-Z4",
            "value": 33.94782224658786,
            "unit": "iter/sec",
            "range": "stddev: 0.000494109941424692",
            "extra": "mean: 29.456970545452627 msec\nrounds: 33"
          },
          {
            "name": "Mosaic-Z5",
            "value": 32.14425706112744,
            "unit": "iter/sec",
            "range": "stddev: 0.0004446244592879219",
            "extra": "mean: 31.109756187500004 msec\nrounds: 32"
          },
          {
            "name": "Mosaic-Z6",
            "value": 31.888195077278603,
            "unit": "iter/sec",
            "range": "stddev: 0.00043218780554105633",
            "extra": "mean: 31.35956731249845 msec\nrounds: 32"
          },
          {
            "name": "Search-Z0",
            "value": 39.23344975536092,
            "unit": "iter/sec",
            "range": "stddev: 0.0008783312559746878",
            "extra": "mean: 25.488454526315476 msec\nrounds: 38"
          },
          {
            "name": "Search-Z1",
            "value": 73.08913550114606,
            "unit": "iter/sec",
            "range": "stddev: 0.0005743992085331212",
            "extra": "mean: 13.681924038960888 msec\nrounds: 77"
          },
          {
            "name": "Search-Z2",
            "value": 74.9219839542347,
            "unit": "iter/sec",
            "range": "stddev: 0.006239008079026225",
            "extra": "mean: 13.34721729487088 msec\nrounds: 78"
          },
          {
            "name": "Search-Z3",
            "value": 92.30138164061235,
            "unit": "iter/sec",
            "range": "stddev: 0.0005611174850198723",
            "extra": "mean: 10.834074010870523 msec\nrounds: 92"
          },
          {
            "name": "Search-Z4",
            "value": 99.72033795581211,
            "unit": "iter/sec",
            "range": "stddev: 0.00046624356438972574",
            "extra": "mean: 10.028044634617244 msec\nrounds: 104"
          },
          {
            "name": "Search-Z5",
            "value": 96.72918130205053,
            "unit": "iter/sec",
            "range": "stddev: 0.0008621043042644232",
            "extra": "mean: 10.338141877551497 msec\nrounds: 98"
          },
          {
            "name": "Search-Z6",
            "value": 97.83107196132572,
            "unit": "iter/sec",
            "range": "stddev: 0.0005349653478467546",
            "extra": "mean: 10.221701346534534 msec\nrounds: 101"
          }
        ]
      }
    ]
  }
}