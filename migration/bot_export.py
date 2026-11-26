# Bot Export
# USAGE:
# - python bot_export.py
# - python bot_export.py <export path>
# Exports the entirety of your IdiotNet database into a dataset for training IdiotBot in unsloth
# Will export to dataset.json if not specified
# thanks to https://lablab.build/ai-tutorials/fine-tuning-tinyllama for help with training the bot

import os
import sys
import json
import psycopg2
from dotenv import load_dotenv

# Bio: IdiotBot writes a bio for itself upon first run
instruction_bio = "Write a short social media bio about yourself, pretending you are a human. Give yourself a made up name and personal details."
input_bio = ""
outputs_bio = {}

# Post: IdiotBot writes a post spontaneously, with no external trigger
instruction_post = "Make an open-ended post about anything you want, given the following context."
input_post = "Date/time: {}"
outputs_post = {}

# Comment: IdiotBot writes a comment on the post that is @mention'ing it
instruction_comment = "Make a comment response for the following social media post."
input_comment = "Title: {} | Author: {} | Date Posted: {} | Content: {}"
outputs_comments = {}

# Reply: IdiotBot replies to a comment that is @mention'ing it
instruction_reply = "Make a comment reply to the following social media comment."
input_reply = "Author: {} | Date Posted: {} | Content: {}"
outputs_replies = {}

# dataset to be serialized in json
dataset = []

# make sure data isn't empty
def checkData(x:str):
    return x is not None and x != ""

def main(args:list[str]):
    # get export argument
    export_path = "./dataset.json"
    if len(args) == 1:
        export_path = args[0]
    elif len(args) > 1:
        raise ValueError("Incorrect number of arguments.")

    # get db connection
    load_dotenv()
    connection = psycopg2.connect(
                    dbname=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    host= os.getenv("DB_HOST"),
                    port=os.getenv("DB_PORT")
                )
    cursor = connection.cursor()
    print("Beginning export!")

    # get all user bios (simplest part)
    cursor.execute("SELECT bio from users")
    outputs_replies = cursor.fetchall()
    for output_reply in outputs_replies:
        bio = output_reply[0]
        if checkData(bio):
            dataset.append({
                        "instruction": instruction_bio,
                        "input": input_bio,
                        "output": bio
                    })

    # the models at this point are really poorly optimized so we will just use raw requests instead of stuff like Post.read(...)
    # this code would be a lot simpler if the models had a multi-request option, maybe we will do that in the future...
    # (actually they did in the early days)
    # get user posts (slightly more complex)
    cursor.execute("SELECT content, author, date_posted from posts")
    outputs_posts = cursor.fetchall()
    for output_post in outputs_posts:
        content = output_post[0]
        date_posted = output_post[2]
        if checkData(content): # only add posts with content
            dataset.append({
                        "instruction": instruction_post,
                        "input": input_post.format(date_posted),
                        "output": content
                    })

    # get comments on posts (big chonker request)
    cursor.execute("""
            SELECT 
                p.title AS title,
                p.content AS post_content, 
                p.date_posted AS post_date,
                post_author.username AS post_username,
                c.content AS comment_content
            FROM posts p
            INNER JOIN users post_author ON p.author = post_author.id
            LEFT JOIN comments c ON p.id = c.comment_page
        """)
    outputs_comments = cursor.fetchall()
    for output_comment in outputs_comments:
        title = output_comment[0]
        post_content = output_comment[1]
        date_posted = output_comment[2]
        author = output_comment[3]
        comment_content = output_comment[4]
        if checkData(comment_content): # only add non-null comments
            dataset.append({
                        "instruction": instruction_comment,
                        "input": input_comment.format(title, author, date_posted, post_content),
                        "output": comment_content
                    })

    # get replies to comments (biggest mega fat chonker request)
        cursor.execute("""
                SELECT 
                    root_author.username AS root_author,
                    root.date_posted     AS root_date_posted,
                    root.content         AS root_content,
                    reply.content          AS reply_content
                FROM comments reply
                INNER JOIN comments root ON reply.root_comment = root.id
                INNER JOIN users root_author ON root.author = root_author.id
                WHERE reply.root_comment != -1;
            """)
        outputs_replies = cursor.fetchall()
        for output_reply in outputs_replies:
            author = output_reply[0]
            date_posted = output_reply[1]
            root_content = output_reply[2]
            reply_content = output_reply[3]
            if checkData(reply_content): # only add non-null comments
                dataset.append({
                            "instruction": instruction_reply,
                            "input": input_reply.format(author, date_posted, root_content),
                            "output": reply_content
                        })

    # FINALLY: EXPORT THE DATA!
    try:
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=4, ensure_ascii=False)
    except Exception as e:
        raise IOError(f"Could not export file to {export_path} for reason: {str(e)}")
    finally:
        # close up shop...
        cursor.close()
        connection.close()

    print("Export complete!")
    

if __name__ == '__main__':
    main(sys.argv[1:])