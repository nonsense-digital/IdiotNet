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
    filename      text default ''::text,
    author        integer not null,
    date_uploaded timestamp
);

create table posts
(
    id          integer generated always as identity (minvalue 0)
        constraint posts_pk
            primary key,
    title       text default 'Untitled Post'::text not null,
    content     text default ''::text              not null,
    author      integer                            not null,
    date_posted timestamp
);

create table tokens
(
    id          uuid      not null,
    user_id     integer   not null,
    valid_until timestamp not null
);

create table users
(
    id            integer generated always as identity (minvalue 0),
    username      varchar(15)  not null,
    email         varchar(60),
    date_created  timestamp    not null,
    password_hash varchar(255) not null,
    bio           text default ''::text,
    constraint users_pk
        primary key (id, username)
);

create table config
(
    key   varchar(20) not null
        constraint config_pk
            primary key,
    value varchar(255)
);

INSERT INTO config (key, value) VALUES ('join_code', null);
INSERT INTO config (key, value) VALUES ('version', '1.0');

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

create table attachments
(
    id      integer generated always as identity (minvalue 0)
        constraint attachments_pk
            primary key,
    image   integer,
    post    integer not null,
    caption text default ''::text
);


