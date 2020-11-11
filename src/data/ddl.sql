create table `ethan_wolfe` (
    `user` varchar(11) default 'Ethan Wolfe',
    PRIMARY KEY (user)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

insert into `ethan_wolfe` value ();

create table `titles` (
    `title_id` varchar(10) not null,
    `type` varchar(15) default null,
    `primary_title` varchar(400) default null,
    `original_title` varchar(400) default null,
    `is_adult` int(11) default null,
    `premiered` int(11) default null,
    `ended` int(11) default null,
    `runtime_minutes` int(11) default null,
    `genres` varchar(32) default null,
    `user` varchar(11) default 'Ethan Wolfe',
    primary key (title_id),
    index `ix_primary`(title_id),
    foreign key (user) references ethan_wolfe(user)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

create table `episodes` (
    `episode_title_id` varchar(10) default null,
    `show_title_id` varchar(10) default null,
    `season_number` int(11) default null,
    `episode_number` int(11) default null,
    `user` varchar(11) default 'Ethan Wolfe',
    primary key (episode_title_id),
    foreign key (show_title_id) references titles(title_id),
    foreign key (user) references ethan_wolfe(user)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

create table `ratings` (
    `title_id` varchar(10) not null,
    `rating` float default null,
    `votes` int(11) default null,
    `user` varchar(11) default 'Ethan Wolfe',
    primary key (title_id),
    index `ix_primary`(title_id),
    foreign key (title_id) references titles(title_id),
    foreign key (user) references ethan_wolfe(user)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

create table `akas` (
    `title_id` varchar(10) default null,
    `title` varchar(553) default null,
    `region` varchar(4) default null,
    `language` varchar(3) default null,
    `types` varchar(16) default null,
    `attributes` varchar(62) default null,
    `is_original_title` int(11) default null,
    `user` varchar(11) default 'Ethan Wolfe',
    index `akas_title_id`(title_id),
    index `akas_title`(title),
    foreign key (title_id) references titles(title_id),
    foreign key (user) references ethan_wolfe(user)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

create table `people` (
    `person_id` varchar(10) not null,
    `name` varchar(105) default null,
    `born` int(11) default null,
    `died` int(11) default null,
    `user` varchar(11) default 'Ethan Wolfe',
    primary key (person_id),
    index `ix_primary`(person_id),
    index `people_name`(name),
    foreign key (user) references ethan_wolfe(user)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

create table `crew` (
    `title_id` varchar(10) default null,
    `person_id` varchar(10) default null,
    `category` varchar(20) default null,
    `job` varchar(286) default null,
    `user` varchar(11) default 'Ethan Wolfe',
    index `crew_title_id` (title_id),
    index `crew_person_id` (person_id),
    foreign key (title_id) references titles(title_id),
    foreign key (person_id) references people(person_id),
    foreign key (user) references ethan_wolfe(user)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;