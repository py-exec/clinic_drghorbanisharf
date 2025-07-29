#!/bin/bash

APPS=(
  accounts
  patient
  reception
  doctors
  appointments
  accounting
  inventory
  prescriptions
  ecg
  echo_tte
  echo_tee
  exercise_stress_test
  holter
  holter_bp
  holter_hr
  tilt
  clinic_messenger
  menu
  staffs
)

echo "=== MAKEMIGRATIONS ==="
for app in "${APPS[@]}"
do
  echo "--- makemigrations $app ---"
  python manage.py makemigrations "$app"
done

echo ""
echo "=== MIGRATE ==="
for app in "${APPS[@]}"
do
  echo "--- migrate $app ---"
  python manage.py migrate "$app"
done
