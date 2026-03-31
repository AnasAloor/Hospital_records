SELECT
    ti.month                                        AS "Month",
    ti.patient_id                                   AS "Patient ID",
    ti.access_type                                  AS "Access Type",
    ti.facility_id                                  AS "Facility ID",
    ti.assigned_facility_flag                       AS "Assigned Facility Flag",
    ti.total_tx                                     AS "Total Treatments",
    ti.total_mtx                                    AS "Missed Treatments",
    ti.total_scheduled_tx                           AS "Scheduled Treatments",
    ti.tx_percent_excessive_fluid_gain              AS "% Excessive Fluid Gain",
    ti.frequent_excessive_fluid_gain_flag           AS "Frequent Fluid Gain Flag",
    ti.tx_percent_pw_above_tw                       AS "% Post-Weight Above Target",
    ti.frequent_pw_above_tw_flag                    AS "Frequent Weight Above Target Flag",

    d.age                                           AS "Age",
    d.sex                                           AS "Sex",
    d.race                                          AS "Race",
    d.fdode                                         AS "First Dialysis Date",

    l.albumin                                       AS "Albumin",
    l.hemoglobin                                    AS "Hemoglobin",
    l.hematocrit                                    AS "Hematocrit",
    l.ktv_type                                      AS "KTV Type",
    l.ktv                                           AS "KTV (Dialysis Dose)",

    ai.inpatient_admits                             AS "Inpatient Admits",
    ai.bsi_event                                    AS "BSI Event",

    fi.state                                        AS "State",
    CASE fi.region_id
        WHEN 'A' THEN 'Washington (Region A)'
        WHEN 'B' THEN 'Alabama (Region B)'
        ELSE fi.region_id
    END                                             AS "Region",
    fi.date_open                                    AS "Facility Open Date",
    fi.monday                                       AS "Open Monday",
    fi.tuesday                                      AS "Open Tuesday",
    fi.wednesday                                    AS "Open Wednesday",
    fi.thursday                                     AS "Open Thursday",
    fi.friday                                       AS "Open Friday",
    fi.saturday                                     AS "Open Saturday",
    fi.sunday                                       AS "Open Sunday",

    CASE d.sex
        WHEN 'M' THEN 'Male'
        WHEN 'F' THEN 'Female'
        ELSE d.sex
    END                                             AS "Gender",

    CASE d.race
        WHEN 'W' THEN 'White'
        WHEN 'B' THEN 'Black'
        WHEN 'H' THEN 'Hispanic'
        WHEN 'A' THEN 'Asian'
        WHEN 'O' THEN 'Other'
        ELSE d.race
    END                                             AS "Race (Full Name)",

    CASE l.ktv_type
        WHEN 'sp'  THEN 'Single-Pool'
        WHEN 'std' THEN 'Standard'
        ELSE l.ktv_type
    END                                             AS "KTV Method"

FROM treatment_info ti
LEFT JOIN demographics  d  ON ti.patient_id = d.patient_id  AND ti.month = d.month
LEFT JOIN labs          l  ON ti.patient_id = l.patient_id  AND ti.month = l.month
LEFT JOIN admit_info    ai ON ti.patient_id = ai.patient_id AND ti.month = ai.month
LEFT JOIN facility_info fi ON ti.facility_id = fi.facility_id