CREATE DATABASE IF NOT EXISTS my_db;

GRANT ALL PRIVILEGES ON my_db.* TO 'my_user'@'%' IDENTIFIED BY '123';
FLUSH PRIVILEGES;
USE application;

CREATE TABLE IF NOT EXISTS user (
  id int not null auto_increment,
  username varchar(50),
  password varchar(60),
  primary key (id)
);


CREATE TABLE IF NOT EXISTS application (
  id int(10) unsigned NOT NULL AUTO_INCREMENT,
  name varchar(128) NOT NULL DEFAULT '',
  user_id int not null,
  phone varchar(32) NOT NULL,
  email varchar(200) NOT NULL,
  birthday date,
  sex varchar(3) NOT NULL,
  fav_lang varchar(20) NOT NULL DEFAULT "Rust",
  bio text default ".",
  PRIMARY KEY (id),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);


