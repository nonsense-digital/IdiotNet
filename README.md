# IdiotNet
IdiotNet is a really stupid social media, made by Nonsense Digital.
You can sign up, create posts, upload images, customize your bio, comment, like, and follow.
It also has an admin panel to manage user ban/mutes and to remove inappropriate content.
It used to be really insecure, and probably still is, but since then a lot of the bugs have been ironed out.

## Installation
IdiotNet requires the following to run for a development server:
- PostgreSQL 18.1
- Python 3.12
  - All requisite packages (see [requirements.txt](requirements.txt) )

### Setup for Development
Once you have Python and Postgres installed, you can run the following:
1. Download the files with  `git clone https://github.com/nonsense-digital/IdiotNet.git`
2. Once downloaded, create a Python venv in the new IdiotNet directory with `python -m venv .venv`
3. Activate your virtual environment:
    - Windows Commandline: `.venv\Scripts\activate`
    - Windows PowerShell: `.venv\Scripts\Activate.ps1`
    - Mac/Linux: `source .venv/bin/activate`
4. Install the required packages with `pip install -r requirements.txt`
5. Follow [this guide](https://www.postgresql.org/docs/current/tutorial-createdb.html) to create a new Postrgres database
6. Set up the database schema with `psql -U <username> -d <database name> -f schema.sql`
7. Once set up, IdiotNet can be run with `python -m flask run --host=0.0.0.0`

Alternatively, you can use the many convenient features in PyCharm to automate these processes.
