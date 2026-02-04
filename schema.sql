create type role as enum ('member', 'moderator', 'admin');

create type punishmenttype as enum ('none', 'mute', 'ban', 'permaban');

-- Source - https://stackoverflow.com/a
-- Posted by catchdave, modified by community. See post 'Timeline' for change history
-- Retrieved 2026-01-10, License - CC BY-SA 4.0

CREATE TEXT SEARCH DICTIONARY english_stem_nostop (
    Template = snowball
    , Language = english
);

CREATE TEXT SEARCH CONFIGURATION public.english_nostop ( COPY = pg_catalog.english );
ALTER TEXT SEARCH CONFIGURATION public.english_nostop
   ALTER MAPPING FOR asciiword, asciihword, hword_asciipart, hword, hword_part, word WITH english_stem_nostop;



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
        setweight(to_tsvector('english_nostop'::regconfig, COALESCE(content, ''::text)), 'B'::"char"))) stored
);

create index idx_posts_ts_nostop
    on posts using gin (ts_nostop);

create table tokens
(
    id          uuid      not null,
    user_id     integer   not null,
    valid_until timestamp not null
);

create table users
(
    id                    integer generated always as identity (minvalue 0),
    username              varchar(15)                           not null,
    email                 varchar(60),
    date_created          timestamp                             not null,
    password_hash         bytea                                 not null,
    bio                   text           default ''::text,
    role                  role           default 'member'::role not null,
    punishment_status     punishmenttype default 'none'::punishmenttype,
    punishment_expiration timestamp default '1914-06-28 10:45:00.000000',
    punishment_reason varchar(255) default '',
    constraint users_pk
        primary key (id, username)
);

create table follows
(
    id            integer,
    follower      integer not null,
    following     integer not null,
    date_followed timestamp
);

create table likes
(
    id         integer,
    liker      integer not null,
    liked      integer not null,
    date_liked timestamp
);

create table config
(
    key   varchar(20) not null
        constraint config_pk
            primary key,
    value varchar(255)
);

create table clients
(
    ip_address            inet not null
        constraint clients_pk
            primary key,
    last_accessed         timestamp,
    punishment_status     punishmenttype default 'none',
    punishment_expiration timestamp default '1914-06-28 10:45:00.000000',
    punishment_reason varchar(255) default '',
    rate_limits           integer default 0
);