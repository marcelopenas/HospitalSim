CREATE DATABASE IF NOT EXISTS `hospitalsim`
    CHARACTER SET utf8mb4;

USE `hospitalsim`;

CREATE TABLE IF NOT EXISTS `hospital` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200) NOT NULL,
    `location` VARCHAR(500) NOT NULL,
    `capacity` INT NOT NULL,

    PRIMARY KEY (`id`),
    CONSTRAINT `uq_hospital_name` UNIQUE (`name`),
    CONSTRAINT `uq_hospital_location` UNIQUE (`location`),
    CONSTRAINT `ck_hospital_capacity`
        CHECK (`capacity` >= 0)
) ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `role` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `description` VARCHAR(500) NULL,
    `access_type` CHAR(1) NOT NULL,

    PRIMARY KEY (`id`),
    CONSTRAINT `uq_role_name` UNIQUE (`name`),
    CONSTRAINT `ck_role_access_type`
        CHECK (`access_type` IN ('A', 'B', 'C'))
) ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `staff` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `first_name` VARCHAR(100) NOT NULL,
    `last_name` VARCHAR(100) NOT NULL,
    `hospital_id` INT NOT NULL,
    `date_of_admission` DATE NOT NULL,
    `last_check_in` DATETIME(6) NULL,
    `salary` DECIMAL(12, 2) NOT NULL,

    PRIMARY KEY (`id`),
    KEY `idx_staff_hospital` (`hospital_id`),

    CONSTRAINT `ck_staff_salary`
        CHECK (`salary` >= 0),

    CONSTRAINT `fk_staff_hospital`
        FOREIGN KEY (`hospital_id`)
        REFERENCES `hospital` (`id`)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
) ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `patient` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `first_name` VARCHAR(100) NOT NULL,
    `last_name` VARCHAR(100) NOT NULL,
    `date_of_birth` DATE NOT NULL,
    `staff_id` INT NULL,
    `hospital_id` INT NOT NULL,
    `image_blob` BLOB NOT NULL,

    PRIMARY KEY (`id`),
    KEY `idx_patient_staff` (`staff_id`),
    KEY `idx_patient_hospital` (`hospital_id`),

    CONSTRAINT `fk_patient_staff`
        FOREIGN KEY (`staff_id`)
        REFERENCES `staff` (`id`)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    CONSTRAINT `fk_patient_hospital`
        FOREIGN KEY (`hospital_id`)
        REFERENCES `hospital` (`id`)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
) ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `staff_roles` (
    `staff_id` INT NOT NULL,
    `role_id` INT NOT NULL,

    PRIMARY KEY (`staff_id`, `role_id`),
    KEY `idx_staff_roles_role` (`role_id`),

    CONSTRAINT `fk_staff_roles_staff`
        FOREIGN KEY (`staff_id`)
        REFERENCES `staff` (`id`)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    CONSTRAINT `fk_staff_roles_role`
        FOREIGN KEY (`role_id`)
        REFERENCES `role` (`id`)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
) ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `app_state` (
    `id` INT NOT NULL,
    `was_initialized` BOOLEAN NOT NULL,

    PRIMARY KEY (`id`)
) ENGINE = InnoDB;
