import requests

def get_goodreads_data(isbn):
    """This function uses goodreads API to get number of reviews and grade"""
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "sWSqWzJFOsXzLJL3YgNN2Q", "isbns": isbn}).json()
    return res['books'][0]['work_ratings_count'], res['books'][0]['average_rating']
