create table public.comments
(
    id           integer generated always as identity
        constraint comments_pk
            primary key,
    content      text    default ''::text,
    author       integer                       not null,
    root_comment integer default '-1'::integer not null,
    date_posted  timestamp                     not null,
    comment_type integer default 0             not null,
    comment_page integer                       not null
);

alter table public.comments
    owner to porte;

create table public.images
(
    id            integer generated always as identity
        constraint images_pk
            primary key,
    title         text default ''::text,
    caption       text default ''::text,
    author        integer not null,
    date_uploaded timestamp
);

alter table public.images
    owner to porte;

create table public.posts
(
    id          integer generated always as identity
        constraint posts_pk
            primary key,
    title       text    default 'Untitled Post'::text not null,
    content     text    default ''::text              not null,
    author      integer                               not null,
    date_posted timestamp,
    likes       integer default 0
);

alter table public.posts
    owner to porte;

create table public.tokens
(
    id          uuid      not null,
    user_id     integer   not null,
    valid_until timestamp not null
);

alter table public.tokens
    owner to porte;

create table public.users
(
    id            integer generated always as identity,
    username      varchar(15)                       not null,
    email         varchar(60),
    date_created  timestamp                         not null,
    password_hash varchar(255)                      not null,
    posts         integer[] default '{}'::integer[] not null,
    followers     integer[] default '{}'::integer[] not null,
    following     integer[] default '{}'::integer[] not null,
    liked_posts   integer[] default '{}'::integer[] not null,
    bio           text      default ''::text,
    constraint users_pk
        primary key (id, username)
);

alter table public.users
    owner to porte;

