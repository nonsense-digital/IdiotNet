-- The following was added to the schema in the notifications update, and so this script must be run to set it up on an older db

create type message_type as enum ('follow', 'like', 'post_comment', 'comment_reply', 'watched_post', 'mention', 'admin', 'custom');
create table notifications
(
    id           integer generated always as identity (minvalue 0),
    message_type message_type default 'custom'::message_type               not null,
    message      varchar(255) default 'idiotic message'::character varying not null,
    user_id      integer                                                   not null,
    date_sent    timestamp                                                 not null

);

create table watches
(
    id      integer generated always as identity (minvalue 0),
    post_id integer not null,
    user_id integer not null
);
create table notification_preferences
(
    user_id      integer not null,
    message_type message_type not null,
    enabled      boolean not null,
    constraint notification_preferences_pk
        primary key (user_id, message_type)
);

