-- Synthetic demo schema v3. MySQL 8.4/InnoDB target; NOT server-validated.

-- Apply to an empty isolated staging database. Do not overwrite production databases.

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
  CONSTRAINT `fk_demo_events_0` FOREIGN KEY (`entity`,`id`) REFERENCES `demo_records` (`entity`,`id`),
  CHECK (JSON_VALID(`payload`))
) ENGINE=InnoDB;

CREATE TABLE `demo_plan_versions` (
  `entity` VARBINARY(128) NOT NULL,
  `id` VARBINARY(128) NOT NULL,
  `version` INT UNSIGNED NOT NULL,
  `status` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `name` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `category` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `level` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `compiled_date` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `author_unit` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `accident_type` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `scope` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `commander` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `contact` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `created_at` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `published_at` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`entity`,`id`,`version`),
  CONSTRAINT `fk_demo_plan_versions_0` FOREIGN KEY (`entity`,`id`) REFERENCES `demo_records` (`entity`,`id`),
  CHECK (`entity` = BINARY 'plans'),
  CHECK (`version` > 0),
  CHECK (`status` IN ('draft','review','approved','published','historical'))
) ENGINE=InnoDB;

CREATE TABLE `demo_plan_heads` (
  `entity` VARBINARY(128) NOT NULL,
  `id` VARBINARY(128) NOT NULL,
  `current_version` INT UNSIGNED NOT NULL,
  `published_version` INT UNSIGNED NULL,
  PRIMARY KEY (`entity`,`id`),
  CONSTRAINT `fk_demo_plan_heads_0` FOREIGN KEY (`entity`,`id`,`published_version`) REFERENCES `demo_plan_versions` (`entity`,`id`,`version`),
  CONSTRAINT `fk_demo_plan_heads_1` FOREIGN KEY (`entity`,`id`,`current_version`) REFERENCES `demo_plan_versions` (`entity`,`id`,`version`)
) ENGINE=InnoDB;

CREATE TABLE `demo_plan_steps` (
  `entity` VARBINARY(128) NOT NULL,
  `id` VARBINARY(128) NOT NULL,
  `version` INT UNSIGNED NOT NULL,
  `position` INT UNSIGNED NOT NULL,
  `title` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `department` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `content` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`entity`,`id`,`version`,`position`),
  CONSTRAINT `fk_demo_plan_steps_0` FOREIGN KEY (`entity`,`id`,`version`) REFERENCES `demo_plan_versions` (`entity`,`id`,`version`),
  CHECK (`position` >= 0)
) ENGINE=InnoDB;

CREATE TABLE `demo_plan_reviews` (
  `entity` VARBINARY(128) NOT NULL,
  `id` VARBINARY(128) NOT NULL,
  `version` INT UNSIGNED NOT NULL,
  `record_revision` INT UNSIGNED NOT NULL,
  `at` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `decision` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `review_date` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `opinion` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `notified` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `notice_units` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `filing_department` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `filing_kind` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `evaluation_status` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `evaluation_cycle` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `evaluation_opinion` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `last_filed_date` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `first_filed_date` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `last_evaluated_date` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `reviewed_form` LONGBLOB NOT NULL,
  `form_sha256` CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  PRIMARY KEY (`entity`,`id`,`record_revision`),
  CONSTRAINT `fk_demo_plan_reviews_0` FOREIGN KEY (`entity`,`id`,`record_revision`) REFERENCES `demo_events` (`entity`,`id`,`revision`),
  CONSTRAINT `fk_demo_plan_reviews_1` FOREIGN KEY (`entity`,`id`,`version`) REFERENCES `demo_plan_versions` (`entity`,`id`,`version`),
  CHECK (`decision` IN ('approve','reject'))
) ENGINE=InnoDB;

CREATE TABLE `demo_plan_materials` (
  `entity` VARBINARY(128) NOT NULL,
  `id` VARBINARY(128) NOT NULL,
  `material_id` VARBINARY(128) NOT NULL,
  `record_revision` INT UNSIGNED NOT NULL,
  `name` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `media_type` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `bytes` INT UNSIGNED NOT NULL,
  `sha256` CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `created_at` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `description` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `payload` LONGBLOB NOT NULL,
  PRIMARY KEY (`entity`,`id`,`material_id`),
  CONSTRAINT `fk_demo_plan_materials_0` FOREIGN KEY (`entity`,`id`,`record_revision`) REFERENCES `demo_events` (`entity`,`id`,`revision`),
  CHECK (`bytes` > 0 AND `bytes` <= 2097152),
  CHECK (OCTET_LENGTH(`payload`) = `bytes`)
) ENGINE=InnoDB;

CREATE TABLE `demo_plan_version_materials` (
  `entity` VARBINARY(128) NOT NULL,
  `id` VARBINARY(128) NOT NULL,
  `version` INT UNSIGNED NOT NULL,
  `material_id` VARBINARY(128) NOT NULL,
  PRIMARY KEY (`entity`,`id`,`version`,`material_id`),
  CONSTRAINT `fk_demo_plan_version_materials_0` FOREIGN KEY (`entity`,`id`,`material_id`) REFERENCES `demo_plan_materials` (`entity`,`id`,`material_id`),
  CONSTRAINT `fk_demo_plan_version_materials_1` FOREIGN KEY (`entity`,`id`,`version`) REFERENCES `demo_plan_versions` (`entity`,`id`,`version`)
) ENGINE=InnoDB;

CREATE TABLE `demo_plan_review_materials` (
  `entity` VARBINARY(128) NOT NULL,
  `id` VARBINARY(128) NOT NULL,
  `record_revision` INT UNSIGNED NOT NULL,
  `material_id` VARBINARY(128) NOT NULL,
  PRIMARY KEY (`entity`,`id`,`record_revision`,`material_id`),
  CONSTRAINT `fk_demo_plan_review_materials_0` FOREIGN KEY (`entity`,`id`,`material_id`) REFERENCES `demo_plan_materials` (`entity`,`id`,`material_id`),
  CONSTRAINT `fk_demo_plan_review_materials_1` FOREIGN KEY (`entity`,`id`,`record_revision`) REFERENCES `demo_plan_reviews` (`entity`,`id`,`record_revision`)
) ENGINE=InnoDB;
