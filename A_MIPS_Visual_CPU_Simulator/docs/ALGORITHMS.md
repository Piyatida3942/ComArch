# Algorithms

Factorial: repeated addition in nested loops, without MUL.

nCr Factorial-Based: call factorial three times, then divide via repeated addition.

nCk Optimized: choose a=min(k,n-k), b=max(k,n-k), multiply only needed terms using repeated addition and divide by a! using repeated addition. Handles k=0 as 1. Some n≥18 cases trigger signed 32-bit overflow.

Dynamic instruction count is not actual CPU cycle count or execution time.
