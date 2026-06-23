-- CUSTOM TEXT SEARCH DICTIONARY
-- Similar to the default dictionary in Postgres, except it includes ALL english words
-- this means common articles such as 'a' or 'the' will be included
-- Source - https://stackoverflow.com/questions/1497895/can-i-configure-postgresql-programmatically-to-not-eliminate-stop-words-in-full
-- Posted by catchdave, modified by community. See post 'Timeline' for change history
-- Retrieved 2026-01-10, License - CC BY-SA 4.0
CREATE TEXT SEARCH DICTIONARY english_stem_nostop (
    Template = snowball
    , Language = english
);
CREATE TEXT SEARCH CONFIGURATION public.english_nostop ( COPY = pg_catalog.english );
ALTER TEXT SEARCH CONFIGURATION public.english_nostop
   ALTER MAPPING FOR asciiword, asciihword, hword_asciipart, hword, hword_part, word WITH english_stem_nostop;

-- ROLES
-- Member = Standard, common user that can post, comment, like, etc.
-- Moderator = Can give punishments, censor content, and view IP addresses
-- Admin = Can change user roles and modify server settings
create type role as enum ('member', 'moderator', 'admin');

-- PUNISHMENT TYPES
-- None = normal, no restriction
-- Ban = user/IP cannot access the website
-- Mute = user/IP can view the website, but cannot add or edit any content
-- Permaban = user is permanently removed from the website and all data is erased
create type punishmenttype as enum ('none', 'mute', 'ban', 'permaban');

-- NOTIFICATION MESSAGE TYPES
-- Follow = a user has followed you
-- Like = a user has liked your post
-- Post comment = a user has commented on your post
-- Comment reply = a user has replied to your comment
-- Watched post = there are new comments or edits on a post you are watching
-- Mention = somebody @mentioned you in a post or comment.
-- Admin = an administrative action has been taken against you
-- Custom = idk why not
create type message_type as enum ('follow', 'like', 'post_comment', 'comment_reply', 'watched_post', 'mention', 'admin', 'custom');

-- COMMENTS
-- Text-only, single-line blurbs that users can add to any post
-- Comments can also be replies to other comments, creating "threads" of comments
create table comments
(
    id           integer generated always as identity (minvalue 0)
        constraint comments_pk
            primary key,
    content      text    default ''::text,
    author       integer                       not null,
    root_comment integer default '-1'::integer not null,
    date_posted  timestamp                     not null,
    comment_type integer default 0             not null,
    comment_page integer                       not null
);

-- IMAGES
-- Image files uploading by users
create table images
(
    id            integer generated always as identity (minvalue 0)
        constraint images_pk
            primary key,
    title         text default ''::text,
    author        integer not null
);

-- ATTACHMENTS
-- A link between an image and a post
-- This is necessary to provide quicker concurrent uploading
-- It essentially makes the post creation process more efficient
create table attachments
(
    id       integer generated always as identity (minvalue 0)
        constraint attachments_pk
            primary key,
    post_id  integer not null,
    image_id integer not null
);

-- POSTS
-- These are the main pieces of user-generated content on the site. They are tied to users.
create table posts
(
    id            integer generated always as identity (minvalue 0),
    title         text default 'Untitled Post'::text not null,
    content       text default ''::text              not null,
    author        integer                            not null,
    date_posted   timestamp,
    date_modified timestamp,
    ts_nostop     tsvector generated always as ((
        setweight(to_tsvector('english_nostop'::regconfig, COALESCE(title, ''::text)), 'A'::"char") ||
        setweight(to_tsvector('english_nostop'::regconfig, COALESCE(content, ''::text)), 'B'::"char"))) stored,
    approved      boolean default true
);

-- POST INDEXING
-- Indexes the words used so they can be searched
create index idx_posts_ts_nostop
    on posts using gin (ts_nostop);

-- AUTH TOKENS
-- These are stored in cookies, allowing authentication to be remembered on a web browser
-- They expire after 7 days of inactivity
create table tokens
(
    id          uuid      not null,
    user_id     integer   not null,
    valid_until timestamp not null,
    client      inet      not null
);

-- USERS
-- Represents user accounts and their profiles
-- Can be tracked and punished by moderators/admins
create table users
(
    id                    integer generated always as identity (minvalue 0),
    username              varchar(15)                                                               not null,
    email                 varchar(60),
    date_created          timestamp                                                                 not null,
    password_hash         bytea                                                                     not null,
    bio                   text           default ''::text,
    role                  role           default 'member'::role                                     not null,
    punishment_status     punishmenttype default 'none'::punishmenttype                             not null,
    punishment_expiration timestamp      default '1914-06-28 10:45:00'::timestamp without time zone not null,
    punishment_reason     text   default ''::text,
    constraint users_pk
        primary key (id, username)
);

-- DEFAULT ADMIN
-- Once the website is set up, this user's password should be changed immediately for security
-- The default password is "stupid1A@"
INSERT INTO users (username, email, date_created, password_hash, role) VALUES
             ('admin', null, now(), '$2b$12$kqWB4xcHxygsZhFmiAgYc.rWsy1pRvZ5OJFGk837exLsHRvF0SfvO', 'admin');

-- CONFIGURATION
-- Key-value settings for various server-wide functions
create table config
(
    key   varchar(30) not null
        constraint config_pk
            primary key,
    value varchar(255)
);

-- CONFIGURATION VALUES
-- The "version" config value is used to determine the version of the database
-- This is done to prevent version mismatch between the IdiotNet backend and the database schema
-- Other configuration settings are used for website security and moderation
INSERT INTO config VALUES ('version', '1.0');
INSERT INTO config VALUES ('join_code', null);
INSERT INTO config VALUES ('allow_signup', true);
INSERT INTO config VALUES ('approve_posts', false);
INSERT INTO config VALUES ('support_email', null);
INSERT INTO config VALUES ('announcement_banner', null);
INSERT INTO config VALUES ('require_email', false);
INSERT INTO config VALUES ('require_email_verification', false);

-- CLIENTS
-- Keeps track of previously connected IP addresses
-- Used for website security and moderation
create table clients
(
    ip_address            inet not null
        constraint clients_pk
            primary key,
    last_accessed         timestamp,
    punishment_status     punishmenttype default 'none'::punishmenttype,
    punishment_expiration timestamp      default now(),
    punishment_reason     text    default ''::text
);

-- FOLLOWS
-- Keeps track of follower relationships between users
create table follows
(
    id            integer generated always as identity (minvalue 0)
        constraint follows_pk
            primary key,
    follower      integer not null,
    following     integer not null,
    date_followed timestamp
);

-- LIKES
-- Keeps track of like relationships between posts and users
create table likes
(
    id         integer generated always as identity (minvalue 0)
        constraint likes_pk
            primary key,
    liker      integer not null,
    liked      integer not null,
    date_liked timestamp
);

-- VERIFICATION CHALLENGES
-- A token used for email verification
create table verify
(
    id          uuid        not null
        constraint verify_pk
            primary key,
    user_id     integer     not null,
    valid_until timestamp   not null,
    email       varchar(60) not null
);

-- NOTIFICATIONS
-- Private messages that only the recipient can see
-- Can be customized based on notification type in user settings
create table notifications
(
    id           integer generated always as identity (minvalue 0),
    message_type message_type default 'custom'::message_type               not null,
    message      varchar(255) default 'idiotic message'::character varying not null,
    user_id      integer                                                   not null,
    date_sent    timestamp                                                 not null

);

-- WATCHES
-- A relation between a user and post, creating a "watch"
-- This means the user will be notified of any post changes or activity
create table watches
(
    id      integer generated always as identity (minvalue 0),
    post_id integer not null,
    user_id integer not null
);

-- NOTIFICATION PREFERENCES
-- Defaults to true for each category
-- One record per category per user
create table notification_preferences
(
    user_id      integer not null,
    message_type message_type not null,
    enabled      boolean not null,
    constraint notification_preferences_pk
        primary key (user_id, message_type)
);
