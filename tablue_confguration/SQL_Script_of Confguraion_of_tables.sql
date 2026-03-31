SELECT
    ti.month,
    ti.patient_id,
    ti.access_type,
    ti.facility_id,
    ti.assigned_facility_flag,
    ti.total_tx,
    ti.total_mtx,
    ti.total_scheduled_tx,
    ti.tx_percent_excessive_fluid_gain,
    ti.frequent_excessive_fluid_gain_flag,
    ti.tx_percent_pw_above_tw,
    ti.frequent_pw_above_tw_flag,

    d.age,
    d.sex,
    d.race,
    d.fdode,

    l.albumin,
    l.hemoglobin,
    l.hematocrit,
    l.ktv_type,
    l.ktv,

    ai.inpatient_admits,
    ai.bsi_event,

    fi.state,
    fi.region_id,
    fi.date_open,
    fi.monday,
    fi.tuesday,
    fi.wednesday,
    fi.thursday,
    fi.friday,
    fi.saturday,
    fi.sunday

FROM treatment_info ti
LEFT JOIN demographics  d  ON ti.patient_id = d.patient_id  AND ti.month = d.month
LEFT JOIN labs          l  ON ti.patient_id = l.patient_id  AND ti.month = l.month
LEFT JOIN admit_info    ai ON ti.patient_id = ai.patient_id AND ti.month = ai.month
LEFT JOIN facility_info fi ON ti.facility_id = fi.facility_id

