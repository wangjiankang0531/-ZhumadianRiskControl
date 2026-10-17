-- Synthetic demo only; MySQL target preparation, NOT MySQL-server validated.

SET NAMES utf8mb4;

CREATE TABLE `demo_records` (
  `entity` VARBINARY(128) NOT NULL,
  `id` VARBINARY(128) NOT NULL,
  `revision` INT UNSIGNED NOT NULL,
  `enterprise` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `state` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `date` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `payload` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`entity`,`id`),
  KEY `demo_query` (`entity`,`enterprise`,`state`,`date`),
  CHECK (JSON_VALID(`payload`))
) ENGINE=InnoDB;

CREATE TABLE `demo_events` (
  `entity` VARBINARY(128) NOT NULL,
  `id` VARBINARY(128) NOT NULL,
  `revision` INT UNSIGNED NOT NULL,
  `at` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `kind` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `payload` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`entity`,`id`,`revision`),
  CONSTRAINT `fk_demo_record` FOREIGN KEY (`entity`,`id`) REFERENCES `demo_records` (`entity`,`id`),
  CHECK (JSON_VALID(`payload`))
) ENGINE=InnoDB;
