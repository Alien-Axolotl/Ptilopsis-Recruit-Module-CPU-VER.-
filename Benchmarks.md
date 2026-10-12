## Benchmarks

> **Note:** All numbers come from 100 scans on my local machine (Intel Core i5-13420H, NVIDIA RTX 4050). Your results may vary.

| OCR only the tag boxes | OCR the whole screen |
|---|---|
| **206 ms** | 1,800 ms |

**~8.7x faster**

| Fine label search | Brute force |
|---|---|
| **157 ms** | 1,369 ms |

**~8.7x faster**

> Yes, both speedups really do land on 8.7x (8.74x and 8.72x). Pure coincidence, I checked.

### CPU vs. GPU OCR engine

Each engine was run twice; both values are shown.

| | CPU: RapidOCR (i5-13420H) | GPU: EasyOCR (RTX 4050) |
|---|---|---|
| Scan time (median) | **187 / 202 ms** | 202 / 205 ms |
| Frames read exactly | 25/25 | 25/25 |
| Engine load | **0.69 / 0.74 s** | 6.61 / 6.04 s |
| RAM after load | **62 MB** | 802 / 810 MB |
| Peak RAM | **380 MB** | 1,305 / 1,310 MB |

**TL;DR:** Same accuracy however recorded equal or better scan speed, roughly **9x faster startup** and **13x less idle RAM**. That's why RapidOCR on the CPU is the default. The GPU never pulled ahead here (poor GPU version :<).

**In the GPU version's defense, I fine-tuned the CPU version way more.**
