-- XNBY business schema v4; MySQL 8.4/InnoDB target. NOT live-server validated.

-- Run in an empty staging database. DDL and data import are separate steps.

SET NAMES utf8mb4;

CREATE TABLE `xnby_schema` (`id` INT PRIMARY KEY, `version` INT NOT NULL) ENGINE=InnoDB;

INSERT INTO `xnby_schema` VALUES (1,4);

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

CREATE TABLE `issue_materials` (
  `tenant` VARBINARY(128) NOT NULL,
  `issue` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `id` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `revision` INT UNSIGNED NOT NULL,
  `name` VARCHAR(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `media_type` VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `bytes` INT UNSIGNED NOT NULL,
  `sha256` CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `created` VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `actor` VARBINARY(256) NOT NULL,
  `description` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `payload` LONGBLOB NOT NULL,
  PRIMARY KEY (`tenant`,`issue`,`id`),
  KEY `ix_issue_materials_1` (`tenant`,`issue`,`revision`),
  UNIQUE KEY `ix_issue_materials_2` (`tenant`,`issue`,`revision`),
  CONSTRAINT `fk_issue_materials_0` FOREIGN KEY (`tenant`,`issue`,`revision`) REFERENCES `events` (`tenant`,`issue`,`revision`),
  CHECK (`bytes` > 0 AND `bytes` <= 8388608),
  CHECK (OCTET_LENGTH(`payload`) = `bytes`)
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

CREATE TABLE `gas_alerts` (
  `tenant` VARBINARY(128) NOT NULL,
  `id` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `source_system` VARBINARY(256) NOT NULL,
  `source_id` VARBINARY(256) NOT NULL,
  `spatial_id` VARBINARY(256) NOT NULL,
  `source_revision` INT UNSIGNED NOT NULL,
  `revision` INT UNSIGNED NOT NULL,
  `updated` VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `payload` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`tenant`,`id`),
  KEY `ix_gas_alerts_1` (`tenant`,`spatial_id`,`updated`),
  UNIQUE KEY `ix_gas_alerts_2` (`tenant`,`source_system`,`source_id`),
  CHECK (JSON_VALID(`payload`))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

CREATE TABLE `gas_history` (
  `tenant` VARBINARY(128) NOT NULL,
  `event_id` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `revision` INT UNSIGNED NOT NULL,
  `at` VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `actor` VARBINARY(256) NOT NULL,
  `policy` VARBINARY(128) NOT NULL,
  `kind` VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `payload` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `state_sha256` CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  PRIMARY KEY (`tenant`,`event_id`,`revision`),
  CONSTRAINT `fk_gas_history_0` FOREIGN KEY (`tenant`,`event_id`) REFERENCES `gas_alerts` (`tenant`,`id`),
  CHECK (JSON_VALID(`payload`))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

CREATE TABLE `gas_requests` (
  `tenant` VARBINARY(128) NOT NULL,
  `actor` VARBINARY(256) NOT NULL,
  `key` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `event_id` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `digest` CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `result` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`tenant`,`actor`,`key`),
  CONSTRAINT `fk_gas_requests_0` FOREIGN KEY (`tenant`,`event_id`) REFERENCES `gas_alerts` (`tenant`,`id`),
  CHECK (JSON_VALID(`result`))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

CREATE TABLE `gas_outbox` (
  `tenant` VARBINARY(128) NOT NULL,
  `id` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `event_id` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `revision` INT UNSIGNED NOT NULL,
  `target_system` VARBINARY(256) NOT NULL,
  `delivery_state` VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `attempts` INT UNSIGNED NOT NULL,
  `lease_sha256` CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
  `lease_until` VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NULL,
  `next_attempt_at` VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `last_error` VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
  `package_sha256` CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `payload` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`tenant`,`id`),
  KEY `ix_gas_outbox_1` (`tenant`,`delivery_state`,`next_attempt_at`),
  CONSTRAINT `fk_gas_outbox_0` FOREIGN KEY (`tenant`,`event_id`,`revision`) REFERENCES `gas_history` (`tenant`,`event_id`,`revision`),
  CHECK (JSON_VALID(`payload`))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

CREATE TABLE `gas_materials` (
  `tenant` VARBINARY(128) NOT NULL,
  `event_id` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `id` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `revision` INT UNSIGNED NOT NULL,
  `scope` VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `enterprise` VARBINARY(256) NULL,
  `name` VARCHAR(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `media_type` VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `bytes` INT UNSIGNED NOT NULL,
  `sha256` CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `created` VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `actor` VARBINARY(256) NOT NULL,
  `description` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `payload` LONGBLOB NOT NULL,
  PRIMARY KEY (`tenant`,`event_id`,`id`),
  KEY `ix_gas_materials_1` (`tenant`,`event_id`,`scope`,`enterprise`),
  UNIQUE KEY `ix_gas_materials_2` (`tenant`,`event_id`,`revision`),
  CONSTRAINT `fk_gas_materials_0` FOREIGN KEY (`tenant`,`event_id`,`revision`) REFERENCES `gas_history` (`tenant`,`event_id`,`revision`),
  CHECK (`bytes` > 0 AND `bytes` <= 8388608),
  CHECK (OCTET_LENGTH(`payload`) = `bytes`),
  CHECK ((`scope` = 'public' AND `enterprise` IS NULL) OR (`scope` = 'enterprise' AND `enterprise` IS NOT NULL))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

CREATE TABLE `gas_delivery_attempts` (
  `tenant` VARBINARY(128) NOT NULL,
  `request_id` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `attempt` INT UNSIGNED NOT NULL,
  `claimed_at` VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `lease_sha256` CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `lease_until` VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `finished_at` VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin NULL,
  `outcome` VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `error_code` VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
  PRIMARY KEY (`tenant`,`request_id`,`attempt`),
  CONSTRAINT `fk_gas_delivery_attempts_0` FOREIGN KEY (`tenant`,`request_id`) REFERENCES `gas_outbox` (`tenant`,`id`)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
