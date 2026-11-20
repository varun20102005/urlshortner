
import time
import statistics

import requests
import redis


BASE_URL = "http://127.0.0.1:8000"
SHORT_CODE = input("Enter your short code: ")

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

url = f"{BASE_URL}/{SHORT_CODE}"
cache_key = f"url:{SHORT_CODE}"

ITERATIONS = 30


def benchmark_cache_hits():
    times = []

    # Warm the cache first
    requests.get(url, allow_redirects=False)

    for _ in range(ITERATIONS):
        start = time.perf_counter()

        response = requests.get(
            url,
            allow_redirects=False
        )

        end = time.perf_counter()

        if response.status_code != 302:
            raise RuntimeError(
                f"Unexpected status: {response.status_code}"
            )

        times.append((end - start) * 1000)

    return times


def benchmark_cache_misses():
    times = []

    for _ in range(ITERATIONS):
        # Clear the cache before every request
        redis_client.delete(cache_key)

        start = time.perf_counter()

        response = requests.get(
            url,
            allow_redirects=False
        )

        end = time.perf_counter()

        if response.status_code != 302:
            raise RuntimeError(
                f"Unexpected status: {response.status_code}"
            )

        times.append((end - start) * 1000)

    return times


def display_results(name, times):
    print(f"\n{name}")
    print("-" * 35)
    print(f"Average: {statistics.mean(times):.2f} ms")
    print(f"Median:  {statistics.median(times):.2f} ms")
    print(f"Minimum: {min(times):.2f} ms")
    print(f"Maximum: {max(times):.2f} ms")


hit_times = benchmark_cache_hits()
miss_times = benchmark_cache_misses()

display_results("CACHE HIT", hit_times)
display_results("CACHE MISS", miss_times)

hit_avg = statistics.mean(hit_times)
miss_avg = statistics.mean(miss_times)

if miss_avg > 0:
    improvement = ((miss_avg - hit_avg) / miss_avg) * 100

    print("\nPerformance comparison")
    print("-" * 35)
    print(f"Cache hit average:  {hit_avg:.2f} ms")
    print(f"Cache miss average: {miss_avg:.2f} ms")
    print(f"Difference:         {improvement:.2f}%")

    if improvement > 0:
        print("Cache hits were faster in this test.")
    elif improvement < 0:
        print("Cache hits were slower in this test.")
    else:
        print("Both averages were equal.")
