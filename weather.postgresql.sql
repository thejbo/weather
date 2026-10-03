-- Adminer 5.3.0 PostgreSQL 18.6 dump
DROP TABLE IF EXISTS "ambient_weather";

CREATE TABLE "weather"."ambient_weather" (
  "sample" timestamptz NOT NULL,
  "outdoor_temp_f" numeric(5, 2),
  "indoor_temp_f" numeric(5, 2),
  "dew_point_f" numeric(5, 2),
  "wind_speed_mph" numeric(5, 2),
  "wind_gust_mph" numeric(5, 2),
  "wind_direction" smallint,
  "hourly_rain" numeric(5, 2),
  "outdoor_humidity" smallint,
  "indoor_humidity" smallint,
  "uv_index" smallint,
  "solar_radiation" numeric(10, 2),
  "absolute_pressure" numeric(5, 2),
  "device_mac" character(17) NOT NULL,
  CONSTRAINT "idx_17221_primary" PRIMARY KEY ("sample", "device_mac")
) WITH (oids = false);

DROP VIEW IF EXISTS "chill_hours";

CREATE TABLE "chill_hours" (
  "month" double precision,
  "year" double precision,
  "chill_hours" bigint
);

DROP TABLE IF EXISTS "envoy";

CREATE TABLE "weather"."envoy" (
  "lastreportdate" timestamptz NOT NULL,
  "serialnumber" character(12) NOT NULL,
  "lastreportwatts" bigint NOT NULL,
  CONSTRAINT "idx_17232_primary" PRIMARY KEY ("lastreportdate")
) WITH (oids = false);

CREATE INDEX idx_17232_serialnumber ON weather.envoy USING btree (serialnumber);

DROP VIEW IF EXISTS "envoy_by15";

CREATE TABLE "envoy_by15" (
  "time" timestamptz,
  "serialnumber" character(12),
  "array" character(2),
  "lastreportwatts" bigint
);

DROP TABLE IF EXISTS "envoy_panels";

CREATE TABLE "weather"."envoy_panels" (
  "serialnumber" character(12) NOT NULL,
  "array" character(2) NOT NULL,
  CONSTRAINT "idx_17235_primary" PRIMARY KEY ("serialnumber")
) WITH (oids = false);

DROP TABLE IF EXISTS "sdge_usage";

CREATE TABLE "weather"."sdge_usage" (
  "sample_timestamp" timestamptz NOT NULL,
  "usage" numeric(10, 5) NOT NULL,
  "generation" numeric(10, 5) DEFAULT '0.00000' NOT NULL,
  CONSTRAINT "idx_17238_primary" PRIMARY KEY ("sample_timestamp")
) WITH (oids = false);

ALTER TABLE
  ONLY "weather"."envoy"
ADD
  CONSTRAINT "envoy_ibfk_1" FOREIGN KEY (serialnumber) REFERENCES envoy_panels(serialnumber) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE;

DROP TABLE IF EXISTS "chill_hours";

CREATE VIEW "chill_hours" AS
SELECT
  date_part('month' :: text, sample) AS MONTH,
  date_part('year' :: text, sample) AS year,
  (count(0) / 12) AS chill_hours
FROM
  ambient_weather
WHERE
  (outdoor_temp_f <= (45) :: numeric)
GROUP BY
  (date_part('month' :: text, sample)),
  (date_part('year' :: text, sample))
ORDER BY
  (date_part('year' :: text, sample)) DESC,
  (date_part('month' :: text, sample)) DESC;

DROP TABLE IF EXISTS "envoy_by15";

CREATE VIEW "envoy_by15" AS
SELECT
  date_bin(
    '00:15:00' :: INTERVAL,
    envoy.lastreportdate,
    '1970-01-01 00:00:00+00' :: timestamp WITH time zone
  ) AS "time",
  envoy.serialnumber,
  envoy_panels."array",
  envoy.lastreportwatts
FROM
  (
    envoy
    JOIN envoy_panels ON ((envoy_panels.serialnumber = envoy.serialnumber))
  )
GROUP BY
  envoy_panels."array",
  envoy.lastreportwatts,
  envoy.serialnumber,
  (
    date_bin(
      '00:15:00' :: INTERVAL,
      envoy.lastreportdate,
      '1970-01-01 00:00:00+00' :: timestamp WITH time zone
    )
  )
ORDER BY
  (
    date_bin(
      '00:15:00' :: INTERVAL,
      envoy.lastreportdate,
      '1970-01-01 00:00:00+00' :: timestamp WITH time zone
    )
  ) DESC,
  envoy.serialnumber;

-- 2026-10-02 23:54:16 UTC
