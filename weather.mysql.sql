-- Adminer 5.3.0 MariaDB 11.8.8-MariaDB dump
SET
  NAMES utf8;

SET
  time_zone = '+00:00';

SET
  foreign_key_checks = 0;

SET
  sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

DROP TABLE IF EXISTS `ambient_weather`;

CREATE TABLE `ambient_weather` (
  `sample` datetime NOT NULL,
  `outdoor_temp_f` decimal(5, 2) DEFAULT NULL,
  `indoor_temp_f` decimal(5, 2) DEFAULT NULL,
  `dew_point_f` decimal(5, 2) DEFAULT NULL,
  `wind_speed_mph` decimal(5, 2) DEFAULT NULL,
  `wind_gust_mph` decimal(5, 2) DEFAULT NULL,
  `wind_direction` smallint(6) DEFAULT NULL,
  `hourly_rain` decimal(5, 2) DEFAULT NULL,
  `outdoor_humidity` tinyint(3) UNSIGNED DEFAULT NULL,
  `indoor_humidity` tinyint(3) UNSIGNED DEFAULT NULL,
  `uv_index` tinyint(3) UNSIGNED DEFAULT NULL,
  `solar_radiation` decimal(10, 2) DEFAULT NULL,
  `absolute_pressure` decimal(5, 2) DEFAULT NULL,
  `device_mac` char(17) NOT NULL,
  PRIMARY KEY (`sample`, `device_mac`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb3 COLLATE = utf8mb3_general_ci;

DROP VIEW IF EXISTS `chill_hours`;

CREATE TABLE `chill_hours` (
  `month` int(3),
  `year` int(5),
  `chill_hours` decimal(24, 4)
);

DROP TABLE IF EXISTS `envoy`;

CREATE TABLE `envoy` (
  `lastReportDate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP(),
  `serialNumber` char(12) NOT NULL,
  `lastReportWatts` int(11) NOT NULL,
  PRIMARY KEY (`lastReportDate`),
  KEY `serialNumber` (`serialNumber`),
  CONSTRAINT `envoy_ibfk_1` FOREIGN KEY (`serialNumber`) REFERENCES `envoy_panels` (`serialNumber`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb3 COLLATE = utf8mb3_general_ci;

DROP VIEW IF EXISTS `envoy_by15`;

CREATE TABLE `envoy_by15` (
  `time` datetime
  /* mariadb-5.3 */
,
  `serialNumber` char(12),
  `array` char(2),
  `lastReportWatts` int(11)
);

DROP VIEW IF EXISTS `envoy_by15_old`;

CREATE TABLE `envoy_by15_old` (
  `time` datetime
  /* mariadb-5.3 */
,
  `serialNumber` char(12),
  `lastReportWatts` int(11)
);

DROP TABLE IF EXISTS `envoy_panels`;

CREATE TABLE `envoy_panels` (
  `serialNumber` char(12) NOT NULL,
  `array` char(2) NOT NULL,
  PRIMARY KEY (`serialNumber`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb3 COLLATE = utf8mb3_general_ci;

DROP VIEW IF EXISTS `sdge_summary_tou`;

CREATE TABLE `sdge_summary_tou` (
  `tou_usage` decimal(32, 5),
  `tou_generation` decimal(32, 5),
  `day` varchar(19),
  `TOU` varchar(12)
);

DROP TABLE IF EXISTS `sdge_usage`;

CREATE TABLE `sdge_usage` (
  `sample_timestamp` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00' ON UPDATE CURRENT_TIMESTAMP(),
  `usage` decimal(10, 5) NOT NULL,
  `generation` decimal(10, 5) NOT NULL DEFAULT 0.00000,
  PRIMARY KEY (`sample_timestamp`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb3 COLLATE = utf8mb3_general_ci;

DROP VIEW IF EXISTS `sdge_usage_tou`;

CREATE TABLE `sdge_usage_tou` (
  `sample_timestamp` timestamp,
  `local_timestamp` datetime
  /* mariadb-5.3 */
,
  `usage` decimal(10, 5),
  `generation` decimal(10, 5),
  `TOU` varchar(12)
);

DROP TABLE IF EXISTS `chill_hours`;

CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `chill_hours` AS
SELECT
  MONTH(`ambient_weather`.`sample`) AS `month`,
  year(`ambient_weather`.`sample`) AS `year`,
  count(0) / 12 AS `chill_hours`
FROM
  `ambient_weather`
WHERE
  `ambient_weather`.`outdoor_temp_f` <= 45
GROUP BY
  MONTH(`ambient_weather`.`sample`),
  year(`ambient_weather`.`sample`)
ORDER BY
  year(`ambient_weather`.`sample`) DESC,
  MONTH(`ambient_weather`.`sample`) DESC;

DROP TABLE IF EXISTS `envoy_by15`;

CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `envoy_by15` AS
SELECT
  cast(
    date_format(`envoy`.`lastReportDate`, '%Y-%m-%d %H:00:00') + INTERVAL MINUTE(`envoy`.`lastReportDate`) - MINUTE(`envoy`.`lastReportDate`) MOD 15 MINUTE AS datetime
  ) AS `time`,
  `envoy`.`serialNumber` AS `serialNumber`,
  `envoy_panels`.`array` AS `array`,
  `envoy`.`lastReportWatts` AS `lastReportWatts`
FROM
  (
    `envoy`
    JOIN `envoy_panels` ON(
      `envoy_panels`.`serialNumber` = `envoy`.`serialNumber`
    )
  )
GROUP BY
  `envoy`.`serialNumber`,
  cast(
    date_format(`envoy`.`lastReportDate`, '%Y-%m-%d %H:00:00') + INTERVAL MINUTE(`envoy`.`lastReportDate`) - MINUTE(`envoy`.`lastReportDate`) MOD 15 MINUTE AS datetime
  )
ORDER BY
  cast(
    date_format(`envoy`.`lastReportDate`, '%Y-%m-%d %H:00:00') + INTERVAL MINUTE(`envoy`.`lastReportDate`) - MINUTE(`envoy`.`lastReportDate`) MOD 15 MINUTE AS datetime
  ) DESC,
  `envoy`.`serialNumber`;

DROP TABLE IF EXISTS `envoy_by15_old`;

CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `envoy_by15_old` AS
SELECT
  cast(
    date_format(`envoy`.`lastReportDate`, '%Y-%m-%d %H:00:00') + INTERVAL MINUTE(`envoy`.`lastReportDate`) - MINUTE(`envoy`.`lastReportDate`) MOD 15 MINUTE AS datetime
  ) AS `time`,
  `envoy`.`serialNumber` AS `serialNumber`,
  `envoy`.`lastReportWatts` AS `lastReportWatts`
FROM
  `envoy`
GROUP BY
  `envoy`.`serialNumber`,
  cast(
    date_format(`envoy`.`lastReportDate`, '%Y-%m-%d %H:00:00') + INTERVAL MINUTE(`envoy`.`lastReportDate`) - MINUTE(`envoy`.`lastReportDate`) MOD 15 MINUTE AS datetime
  )
ORDER BY
  cast(
    date_format(`envoy`.`lastReportDate`, '%Y-%m-%d %H:00:00') + INTERVAL MINUTE(`envoy`.`lastReportDate`) - MINUTE(`envoy`.`lastReportDate`) MOD 15 MINUTE AS datetime
  ) DESC,
  `envoy`.`serialNumber`;

DROP TABLE IF EXISTS `sdge_summary_tou`;

CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `sdge_summary_tou` AS
SELECT
  sum(`sdge_usage_tou`.`usage`) AS `tou_usage`,
  sum(`sdge_usage_tou`.`generation`) AS `tou_generation`,
  date_format(
    convert_tz(
      `sdge_usage_tou`.`sample_timestamp`,
      'UTC',
      'America/Los_Angeles'
    ),
    '%Y-%m-%d 00:00:00'
  ) AS `day`,
  `sdge_usage_tou`.`TOU` AS `TOU`
FROM
  `sdge_usage_tou`
GROUP BY
  `sdge_usage_tou`.`TOU`,
  dayofmonth(
    convert_tz(
      `sdge_usage_tou`.`sample_timestamp`,
      'UTC',
      'America/Los_Angeles'
    )
  ),
  MONTH(
    convert_tz(
      `sdge_usage_tou`.`sample_timestamp`,
      'UTC',
      'America/Los_Angeles'
    )
  ),
  year(
    convert_tz(
      `sdge_usage_tou`.`sample_timestamp`,
      'UTC',
      'America/Los_Angeles'
    )
  );

DROP TABLE IF EXISTS `sdge_usage_tou`;

CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `sdge_usage_tou` AS
SELECT
  `sdge_usage`.`sample_timestamp` AS `sample_timestamp`,
  convert_tz(
    `sdge_usage`.`sample_timestamp`,
    'UTC',
    'America/Los_Angeles'
  ) AS `local_timestamp`,
  `sdge_usage`.`usage` AS `usage`,
  `sdge_usage`.`generation` AS `generation`,
CASE
    WHEN cast(
      convert_tz(
        `sdge_usage`.`sample_timestamp`,
        'UTC',
        'America/Los_Angeles'
      ) AS time
    ) BETWEEN '00:00'
    AND '05:59' THEN 'SuperOffPeak'
    WHEN cast(
      convert_tz(
        `sdge_usage`.`sample_timestamp`,
        'UTC',
        'America/Los_Angeles'
      ) AS time
    ) BETWEEN '06:00'
    AND '09:59' THEN 'OffPeak'
    WHEN cast(
      convert_tz(
        `sdge_usage`.`sample_timestamp`,
        'UTC',
        'America/Los_Angeles'
      ) AS time
    ) BETWEEN '10:00'
    AND '13:59' THEN 'SuperOffPeak'
    WHEN cast(
      convert_tz(
        `sdge_usage`.`sample_timestamp`,
        'UTC',
        'America/Los_Angeles'
      ) AS time
    ) BETWEEN '14:00'
    AND '15:59' THEN 'OffPeak'
    WHEN cast(
      convert_tz(
        `sdge_usage`.`sample_timestamp`,
        'UTC',
        'America/Los_Angeles'
      ) AS time
    ) BETWEEN '16:00'
    AND '20:59' THEN 'OnPeak'
    WHEN cast(
      convert_tz(
        `sdge_usage`.`sample_timestamp`,
        'UTC',
        'America/Los_Angeles'
      ) AS time
    ) BETWEEN '21:00'
    AND '23:59' THEN 'OffPeak'
    ELSE 'NA'
  END AS `TOU`
FROM
  `sdge_usage`
ORDER BY
  `sdge_usage`.`sample_timestamp` DESC;

-- 2026-10-02 23:56:45 UTC
