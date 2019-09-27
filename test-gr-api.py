import requests
res = requests.get("https://www.goodreads.com/book/review_counts.json",
                    params={"key": "JH9iy2wj9ikbergydgFqjA", "isbns": "9781632168146"})
print(res.json())
