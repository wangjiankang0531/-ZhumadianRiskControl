-- XNBY business schema v2; MySQL 8.4/InnoDB target. NOT live-server validated.

-- Run in an empty staging database. DDL and data import are separate steps.

SET NAMES utf8mb4;

CREATE TABLE `xnby_schema` (`id` INT PRIMARY KEY, `version` INT NOT NULL) ENGINE=InnoDB;

INSERT INTO `xnby_schema` VALUES (1,2);

CREATE TABLE `issues` (
  `tenant` VARBINARY(128) NOT NULL,
  `id` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `enterprise` VARBINARY(256) NOT NULL,
  `source_system` VARBINARY(256) NOT NULL,
  `source_id` VARBINARY(256) NOT NULL,
  `revision` INT UNSIGNED NOT NULL,
  `updated` VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `payload` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`tenant`,`id`),
  KEY `ix_issues_1` (`tenant`,`enterprise`,`updated`),
  UNIQUE KEY `ix_issues_2` (`tenant`,`enterprise`,`source_system`,`source_id`),
  CHECK (JSON_VALID(`payload`))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

CREATE TABLE `events` (
  `tenant` VARBINARY(128) NOT NULL,
  `issue` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `revision` INT UNSIGNED NOT NULL,
  `at` VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `actor` VARBINARY(256) NOT NULL,
  `policy` VARBINARY(128) NOT NULL,
  `kind` VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `payload` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`tenant`,`issue`,`revision`),
  CONSTRAINT `fk_events_0` FOREIGN KEY (`tenant`,`issue`) REFERENCES `issues` (`tenant`,`id`),
  CHECK (JSON_VALID(`payload`))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

CREATE TABLE `requests` (
  `tenant` VARBINARY(128) NOT NULL,
  `actor` VARBINARY(256) NOT NULL,
  `key` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `digest` CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `enterprise` VARBINARY(256) NOT NULL,
  `result` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`tenant`,`actor`,`key`),
  CHECK (JSON_VALID(`result`))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

CREATE TABLE `dlg_documents` (
  `tenant` VARBINARY(128) NOT NULL,
  `document_id` VARBINARY(128) NOT NULL,
  `revision` INT UNSIGNED NOT NULL,
  `source_sha256` CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `updated` VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `payload` LONGBLOB NOT NULL,
  PRIMARY KEY (`tenant`,`document_id`)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

CREATE TABLE `dlg_versions` (
  `tenant` VARBINARY(128) NOT NULL,
  `document_id` VARBINARY(128) NOT NULL,
  `revision` INT UNSIGNED NOT NULL,
  `source_sha256` CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `updated` VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `payload` LONGBLOB NOT NULL,
  PRIMARY KEY (`tenant`,`document_id`,`revision`),
  CONSTRAINT `fk_dlg_versions_0` FOREIGN KEY (`tenant`,`document_id`) REFERENCES `dlg_documents` (`tenant`,`document_id`)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

CREATE TABLE `dlg_layers` (
  `tenant` VARBINARY(128) NOT NULL,
  `document_id` VARBINARY(128) NOT NULL,
  `layer_id` VARBINARY(256) NOT NULL,
  `sort_index` INT UNSIGNED NOT NULL,
  `name` VARCHAR(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `visible` TINYINT UNSIGNED NOT NULL,
  `locked` TINYINT UNSIGNED NOT NULL,
  `payload` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`tenant`,`document_id`,`layer_id`),
  KEY `ix_dlg_layers_1` (`tenant`,`document_id`,`sort_index`),
  CONSTRAINT `fk_dlg_layers_0` FOREIGN KEY (`tenant`,`document_id`) REFERENCES `dlg_documents` (`tenant`,`document_id`),
  CHECK (JSON_VALID(`payload`))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

CREATE TABLE `dlg_features` (
  `tenant` VARBINARY(128) NOT NULL,
  `document_id` VARBINARY(128) NOT NULL,
  `feature_id` VARBINARY(256) NOT NULL,
  `layer_id` VARBINARY(256) NOT NULL,
  `sort_index` INT UNSIGNED NOT NULL,
  `geometry_type` VARCHAR(8) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `enterprise` VARBINARY(256) NULL,
  `payload` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`tenant`,`document_id`,`feature_id`),
  KEY `ix_dlg_features_1` (`tenant`,`enterprise`),
  KEY `ix_dlg_features_2` (`tenant`,`document_id`,`layer_id`,`sort_index`),
  CONSTRAINT `fk_dlg_features_0` FOREIGN KEY (`tenant`,`document_id`,`layer_id`) REFERENCES `dlg_layers` (`tenant`,`document_id`,`layer_id`),
  CHECK (JSON_VALID(`payload`))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
