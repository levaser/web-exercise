CREATE DATABASE IF NOT EXISTS my_db;

GRANT ALL PRIVILEGES ON my_db.* TO 'my_user'@'%' IDENTIFIED BY '123';
FLUSH PRIVILEGES;
USE application;


CREATE TABLE application (
  id int(10) unsigned NOT NULL AUTO_INCREMENT,
  name varchar(128) NOT NULL DEFAULT '',
  phone varchar(32) NOT NULL,
  email varchar(200) NOT NULL,
  birthday date,
  sex varchar(3) NOT NULL,
  fav_lang varchar(20) NOT NULL DEFAULT "Rust",
  bio text default ".",
  PRIMARY KEY (id)
);
