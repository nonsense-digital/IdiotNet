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

create type role as enum ('member', 'moderator', 'admin');

create type punishmenttype as enum ('none', 'mute', 'ban', 'permaban');

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

create table images
(
    id            integer generated always as identity (minvalue 0)
        constraint images_pk
            primary key,
    title         text default ''::text,
    author        integer not null,
    post          integer not null
);

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

create index idx_posts_ts_nostop
    on posts using gin (ts_nostop);

create table tokens
(
    id          uuid      not null,
    user_id     integer   not null,
    valid_until timestamp not null,
    client      inet      not null
);

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
    punishment_reason     varchar(255)   default ''::character varying,
    constraint users_pk
        primary key (id, username)
);

-- DEFAULT ADMIN
-- Once the website is set up, this user's password should be changed immediately for security
-- The default password is "stupid1A@"
INSERT INTO users (username, email, date_created, password_hash, role) VALUES
             ('admin', null, now(), '$2b$12$kqWB4xcHxygsZhFmiAgYc.rWsy1pRvZ5OJFGk837exLsHRvF0SfvO', 'admin');

create table config
(
    key   varchar(20) not null
        constraint config_pk
            primary key,
    value varchar(255)
);

-- CONFIGURATION VALUES
-- The "version" config value is used to determine the version of the database
-- This is done to prevent version mismatch between the IdiotNet backend and the database schema
INSERT INTO config VALUES ('version', '1.0');
INSERT INTO config VALUES ('join-code', null);
INSERT INTO config VALUES ('allow_signup', true);
INSERT INTO config VALUES ('approve_posts', false);

create table clients
(
    ip_address            inet not null
        constraint clients_pk
            primary key,
    last_accessed         timestamp,
    punishment_status     punishmenttype default 'none'::punishmenttype,
    punishment_expiration timestamp      default now(),
    punishment_reason     varchar(50)    default ''::character varying,
);

create table follows
(
    id            integer generated always as identity (minvalue 0)
        constraint follows_pk
            primary key,
    follower      integer not null,
    following     integer not null,
    date_followed timestamp
);

create table likes
(
    id         integer generated always as identity (minvalue 0)
        constraint likes_pk
            primary key,
    liker      integer not null,
    liked      integer not null,
    date_liked timestamp
);

