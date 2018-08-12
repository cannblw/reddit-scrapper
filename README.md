# Reddit Scrapper

Reddit scrapper written in Python that collects direct links to all pictures given the subreddit names.
Because this script was written 2 years ago, you may encounter errors due to its nature (it's based on html scrapping). Nonetheless, it's still working.

## How to run

This code depends on the following modules: requests, BeautifulSoup. You will have to install them.

After that, add a list of the subreddits you want to fetch in the file `subreddits.txt` separated by new line.

Then run:

```
python RedditScrapper.py
```

The results will appear inside the `unprocessed_json`directory.
