import asyncpraw

import asyncio
import argparse
import csv
import logging
import os
import dotenv
import datetime

async def get_saved(reddit):
    saved = []
    current_user = await reddit.user.me()
    async for item in current_user.saved(limit=None):
        saved.append(item)
    return saved


def load_reddit():
    # Load environment variables for connecting to bot
    dotenv.load_dotenv()

    try:
        CLIENT_ID = os.environ["CLIENT_ID"]
        CLIENT_SECRET = os.environ["CLIENT_SECRET"]
        USER_AGENT = os.environ["USER_AGENT"]
        USERNAME = os.environ["REDDIT_USERNAME"]
        PASSWORD = os.environ["REDDIT_PASSWORD"]
    except KeyError as keyerror:
        raise Exception("Not all required environment variables have been defined.") from keyerror

    # Get Reddit object
    reddit = asyncpraw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, user_agent=USER_AGENT,
                            username=USERNAME, password=PASSWORD)
    return reddit


def get_post_info(submission):
    # needs to only deal with post submissions, not comments
    post_info = {"title": submission.title, 
                 "author": submission.author,
                 "permalink": submission.permalink, 
                 "url": submission.url, 
                 "subreddit": submission.subreddit, 
                 "is_self": submission.is_self, 
                 "is_nsfw": submission.over_18, 
                 "created_at": datetime.datetime.utcfromtimestamp(submission.created_utc), 
                 "id": submission.id}
    return post_info


def get_comment_info(comment):
    # needs to only deal with post submissions, not comments
    post_info = {"author": comment.author,
                 "body": comment.body, 
                 "permalink": comment.permalink, 
                 "subreddit": comment.subreddit, 
                 "created_at": datetime.datetime.utcfromtimestamp(comment.created_utc), 
                 "id": comment.id}
    return post_info


FIELDNAMES_POSTS = ("title", "author", "permalink", "url", "subreddit", 
                   "is_self", "is_nsfw", "created_at", "id")
FIELDNAMES_COMMENTS = ("author", "body", "permalink", "subreddit", "created_at", "id")


def append_post_csv(rows, filename="posts.csv"):
    with open(filename, "a+", encoding="utf-8", newline="") as csvfile:
        reader = csv.reader(csvfile)
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES_POSTS)  # used fieldnames as header

        # if no lines, then write headers first
        if not len(list(reader)):
            writer.writeheader()  # this only needs to happen on initial writing
        writer.writerows(rows)


def append_comment_csv(rows, filename="comments.csv"):
    with open(filename, "a+", encoding="utf-8", newline="") as csvfile:
        reader = csv.reader(csvfile)
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES_COMMENTS)  # used fieldnames as header

        # if no lines, then write headers first
        if not len(list(reader)):
            writer.writeheader()  # this only needs to happen on initial writing
        writer.writerows(rows)


def load(posts_filename="posts.csv", comments_filename="comments.csv"):
    """
    Load post / comment ids into a set to be used for duplicate checking.
    """
    comments_ids = set()
    posts_ids = set()

    try:
        with open(posts_filename, "r", encoding="utf-8") as posts_csvfile:
            posts_reader = csv.DictReader(posts_csvfile, FIELDNAMES_POSTS)
            for row in posts_reader:
                posts_ids.add(row["id"])
    except FileNotFoundError:
        pass

    try:
        with open(comments_filename, "r", encoding="utf-8") as comments_csvfile:
            comments_reader = csv.DictReader(posts_csvfile, FIELDNAMES_COMMENTS)
            for row in comments_reader:
                comments_ids.add(row["id"])
    except FileNotFoundError:
        pass

    return posts_ids, comments_ids


async def crawl(posts_filename = "posts.csv", comments_filename = "comments.csv"):
    # Set up Reddit object - TODO: Error handling with connection
    reddit = load_reddit()

    # Load previously saved posts
    posts_ids, comments_ids = load()

    # Get saved posts
    saved = await get_saved(reddit)
    post_info = []
    comment_info = []

    # Go through each post, separating them into posts and comments
    for post in saved:
        if isinstance(post, asyncpraw.models.reddit.submission.Submission):
            post_info.append(get_post_info(post))
        elif isinstance(post, asyncpraw.models.reddit.comment.Comment):
            comment_info.append(get_comment_info(post))
        else:
            print(type(post))

    await reddit.close()
    
    # Write info to csv files
    append_post_csv(post_info)
    append_comment_csv(comment_info)

    #Done? I think

def main():
    print("beginning to run!")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(crawl())
    loop.close()


if __name__ == "__main__":
    main()

